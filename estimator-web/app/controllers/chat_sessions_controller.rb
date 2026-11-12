# ── Julián · Sesión 5 · Controlador de la conversación ────────────────────────
#
#   La parte web de la estimación conversacional: crea la sesión en el servicio IA,
#   envía cada turno y guarda el resultado. La web nunca habla con OpenAI directamente.
#
#   · PRESETS son las demos de la sesión: un clic en «Demo presets» rellena el formulario.
#   · Según el modo llama a /estimate (solo actor) o a /estimate-acb (Actor-Critic-Boss).
#   · El tier puede ir en automático o forzado desde el formulario.
#   · Tras cada turno guarda tier, anclas y resumen para pintarlos en el panel lateral.
# ──────────────────────────────────────────────────────────────────────────────

# Conversational estimator UI (Session 5).
#
# A Rails ChatSession mirrors the FastAPI session_id. The full message
# history stays in the FastAPI process; here we persist the latest payload
# (so the user can refresh /chat_sessions/:id and re-read the result) and the
# latest project_metadata snapshot for the side panel.
class ChatSessionsController < ApplicationController
  # The live demos of the session guide, one click away: each preset fills the
  # form (transcript + options + tier + mode); the user still presses Send.
  PRESETS = {
    "crm" => { label: "Baseline · CRM",
      transcript: "Estimar un CRM en React y Postgres para el equipo de ventas, equipo de 3 personas.",
      project_type: "web_saas" },
    "no_nda" => { label: "Tier · sin NDA",
      transcript: "Estimar plataforma de e-commerce con catálogo de 5000 productos, buscador, carrito y checkout con Stripe, panel de administración y emails transaccionales. Equipo de 4 personas con React y Node.",
      project_type: "web_saas" },
    "nda" => { label: "Tier · con NDA",
      transcript: "Heads-up, firmamos NDA antes de la llamada. Estimar plataforma de e-commerce con catálogo de 5000 productos, buscador, carrito y checkout con Stripe, panel de administración y emails transaccionales. Equipo de 4 personas con React y Node.",
      project_type: "web_saas" },
    "devs" => { label: "Tier · developer",
      transcript: "Estimar una plataforma de pedidos con microservicios en Kubernetes, eventos en Kafka y despliegue con Terraform. Equipo de 5 personas.",
      project_type: "web_saas" },
    "acb_ok" => { label: "ACB · CRM + Stripe",
      transcript: "Estimar un CRM en React y Postgres para el equipo de ventas, equipo de 3 personas. Refinar: añadir módulo de facturación con Stripe.",
      project_type: "web_saas", detail_level: "detailed", mode: "acb" },
    "acb_hard" => { label: "ACB · marketplace imposible",
      transcript: "Estimar plataforma compleja: marketplace de servicios con pagos, KYC, chat, app móvil, panel admin, multi-idioma. Equipo de 2 personas en 6 semanas.",
      project_type: "web_saas", detail_level: "detailed", mode: "acb" }
  }.freeze

  def new
    @chat_session = current_chat_session || begin
      remote = EstimatorAi::Client.new.create_session
      ChatSession.create!(remote_session_id: remote["session_id"])
    end
    session[:current_chat_session_id] = @chat_session.id
    @request = request_from_preset
    @latest_estimation = @chat_session.estimations.order(created_at: :desc).first
    @latest_metadata = @chat_session.latest_metadata_hash
  rescue EstimatorAi::Client::ServerError, Faraday::ConnectionFailed, Faraday::TimeoutError => e
    flash.now[:alert] = "AI service unavailable: #{e.message}"
    @chat_session = ChatSession.new
    @request = SessionEstimationRequest.new
    @latest_estimation = nil
    @latest_metadata = {}
    render :new, status: :service_unavailable
  end

  def create
    @chat_session = ChatSession.find(params[:id])
    @request = SessionEstimationRequest.new(session_estimation_request_params)

    unless @request.valid?
      @latest_estimation = @chat_session.estimations.order(created_at: :desc).first
      @latest_metadata = @chat_session.latest_metadata_hash
      render :new, status: :unprocessable_entity
      return
    end

    attachments = Array(params[:attachments]).compact_blank
    tier = params[:tier].presence
    mode = params[:mode].to_s == "acb" ? "acb" : "actor"
    client = EstimatorAi::Client.new
    payload =
      if mode == "acb"
        client.estimate_in_session_acb(@chat_session.remote_session_id, @request,
                                       attachments: attachments, tier: tier)
      else
        client.estimate_in_session(@chat_session.remote_session_id, @request,
                                   attachments: attachments, tier: tier)
      end

    @estimation = @chat_session.estimations.create!(
      description:      @request.transcript,
      project_type:     @request.project_type,
      detail_level:     @request.detail_level,
      output_format:    @request.output_format,
      response_payload: payload,
      prompt_version:   payload["prompt_version"],
      cached:           payload["cached"] || false
    )

    # Refresh the metadata snapshot from FastAPI for the side panel.
    refresh_metadata_snapshot(@chat_session)

    redirect_to chat_session_path(@chat_session)
  rescue EstimatorAi::Client::GuardrailViolation => e
    flash.now[:alert] = e.message
    @request = SessionEstimationRequest.new(session_estimation_request_params)
    @latest_estimation = @chat_session.estimations.order(created_at: :desc).first
    @latest_metadata = @chat_session.latest_metadata_hash
    render :new, status: :unprocessable_entity
  rescue EstimatorAi::Client::InvalidRequest => e
    flash.now[:alert] = e.message
    @request = SessionEstimationRequest.new(session_estimation_request_params)
    @latest_estimation = @chat_session.estimations.order(created_at: :desc).first
    @latest_metadata = @chat_session.latest_metadata_hash
    render :new, status: :unprocessable_entity
  rescue EstimatorAi::Client::SessionNotFound
    # The FastAPI process restarted and lost the session_id. Wipe our
    # mirror and bounce the user back to a fresh conversation.
    @chat_session.destroy
    session.delete(:current_chat_session_id)
    flash[:alert] = "Conversational session expired (FastAPI restart). Started a new one."
    redirect_to new_chat_session_path
  rescue EstimatorAi::Client::ServerError, Faraday::ConnectionFailed, Faraday::TimeoutError => e
    flash.now[:alert] = "AI service unavailable: #{e.message}"
    @request = SessionEstimationRequest.new(session_estimation_request_params)
    @latest_estimation = @chat_session.estimations.order(created_at: :desc).first
    @latest_metadata = @chat_session.latest_metadata_hash
    render :new, status: :service_unavailable
  end

  def show
    @chat_session = ChatSession.find(params[:id])
    @request = request_from_preset
    @latest_estimation = @chat_session.estimations.order(created_at: :desc).first
    @latest_metadata = @chat_session.latest_metadata_hash
    session[:current_chat_session_id] = @chat_session.id
    render :new
  end

  def destroy
    ChatSession.find_by(id: params[:id])&.destroy
    session.delete(:current_chat_session_id)
    redirect_to new_chat_session_path, notice: "Started a new conversation."
  end

  private

  def current_chat_session
    id = session[:current_chat_session_id]
    return nil unless id
    ChatSession.find_by(id: id)
  end

  # Builds the form object, pre-filled from ?preset=… when present.
  def request_from_preset
    preset = PRESETS[params[:preset]]
    @form_mode = preset&.dig(:mode) || "actor"
    @form_tier = preset&.dig(:tier) || "auto"
    return SessionEstimationRequest.new unless preset

    SessionEstimationRequest.new(preset.slice(:transcript, :project_type, :detail_level, :output_format))
  end

  def session_estimation_request_params
    params.require(:session_estimation_request).permit(
      :transcript, :project_type, :detail_level, :output_format
    )
  end

  def refresh_metadata_snapshot(chat_session)
    info = EstimatorAi::Client.new.get_session(chat_session.remote_session_id)
    chat_session.update!(
      latest_metadata: info["metadata"] || {},
      runtime_snapshot: info.except("metadata") || {},
      turn_count: (info["message_count"] || 0) / 2
    )
  rescue StandardError => e
    Rails.logger.warn("Failed to refresh metadata snapshot: #{e.message}")
  end
end
