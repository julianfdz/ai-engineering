# Calidad (Session 11, local): one page per generation-quality technique of the
# session, each driven by an endpoint the IA service already exposes. Nothing is
# persisted: every demo is cheap (the gate without judge and the synthesis are
# deterministic; the judge is one gpt-5-mini call).
#
#   Gate        → POST /v1/estimate/stages/verify  (anchor + optional judge)
#   Conflictos  → POST /v1/estimate/tasks/hours    (consensus + range)
#   Contexto    → POST /v1/estimate/stages/retrieve + /assemble (augment off vs on)
#   Interruptores → GET/PUT /api/v1/config/retrieval (the three S11 toggles)
module Rag
  class QualityController < ApplicationController
    TABS = %w[gate conflict augment toggles].freeze

    # One historical chunk: 120 h ≈ 15 engineer-days. Every gate preset cites it.
    CHUNK_120H = {
      "id" => 1, "content" => "AUTH-001 :: OAuth backend — 120 h", "chunk_type" => "budget_component",
      "distance" => 0.2, "estimated_hours" => 120, "budget_id" => "BUD-1"
    }.freeze

    EVIDENCE = {
      "full" => "AUTH-001 :: OAuth backend — 120 h",   # the whole chunk line: names the work
      "short" => "120 h"                               # the guide's example: only the figure
    }.freeze

    # A preset line is [name, engineer_days]; nil days = an abstention (grounded=false).
    def self.line(name, days, evidence)
      return { "name" => name, "engineer_days" => nil, "grounded" => false, "sources" => [] } if days.nil?

      { "name" => name, "engineer_days" => days, "grounded" => true,
        "sources" => [ { "chunk_id" => "1", "document_id" => "BUD-1", "evidence" => evidence } ] }
    end

    GATE_PRESETS = {
      "false_attribution" => {
        label: "Atribución falsa", hint: "Cita 120 h (≈15 días) y reclama 90 días.",
        lines: [ [ "OAuth login", 90 ] ]
      },
      "honest_slice" => {
        label: "Porción honesta", hint: "Cita 120 h y estima 10 días: menos que la fuente, legítimo.",
        lines: [ [ "OAuth token refresh", 10 ] ]
      },
      "within_tolerance" => {
        label: "Exceso tolerado por el ancla", hint: "Estima 20 días: +33 %, dentro del 50 % del ancla… ¿y el juez?",
        lines: [ [ "OAuth session management", 20 ] ]
      },
      "abstention" => {
        label: "Abstención", hint: "Sin fuente y sin horas: grounded=false.",
        lines: [ [ "Regulatory reporting", nil ] ]
      },
      "all_four" => {
        label: "Las cuatro a la vez", hint: "Una estimación con las cuatro líneas: el informe agregado.",
        lines: [ [ "OAuth login", 90 ], [ "OAuth token refresh", 10 ], [ "OAuth session management", 20 ],
                 [ "Regulatory reporting", nil ] ]
      }
    }.freeze

    # Anchor of every gate preset: the cited chunk's hours in engineer-days (120 h / 8).
    ANCHOR_DAYS = 15.0

    HOURS_PRESETS = {
      "conflict" => { label: "Conflicto 40 h / 90 h (fixture)", module: "Notifications", name: "Real-time notifications delivery service",
                      description: "Multi-channel delivery (push, email, SMS) with a durable queue, per-channel retry and backoff and delivery receipts" },
      "agree" => { label: "Fuentes de acuerdo", module: "Payments & Billing", name: "Payment gateway integration",
                   description: "Stripe checkout and webhooks" },
      "no_match" => { label: "Sin análogo", module: "Physics", name: "Quantum teleporter calibration",
                      description: "calibrate the entanglement field of a teleporter" }
    }.freeze

    AUGMENT_PRESETS = {
      "banking" => "Mobile banking app with OAuth2 authentication, PSD2 open banking and transaction history",
      "ecommerce" => "Headless e-commerce storefront with product catalog, cart, checkout and Stripe payments",
      "telemedicine" => "Telemedicine platform with appointment scheduling, video consultations and HL7 FHIR integration"
    }.freeze

    TOGGLES = {
      "hallucination_gate_enabled" => [ "HALLUCINATION_GATE_ENABLED", "Gate semántico", "Bloque 3 · paso 6.5 del pipeline" ],
      "augmentation_enabled" => [ "AUGMENTATION_ENABLED", "Augmentation", "Bloque 4 · paso 4 del pipeline" ],
      "synthesis_enabled" => [ "SYNTHESIS_ENABLED", "Síntesis (rango)", "Bloque 4 · horas por tarea" ]
    }.freeze

    def show
      @tab = TABS.include?(params[:tab]) ? params[:tab] : "gate"
      prepare_defaults
      load_toggles if @tab == "toggles"
    end

    def verify
      @tab = "gate"
      prepare_defaults
      @gate_preset = GATE_PRESETS.key?(params[:preset]) ? params[:preset] : "all_four"
      @use_judge = params[:use_judge] == "1"
      @evidence_mode = EVIDENCE.key?(params[:evidence]) ? params[:evidence] : "full"
      @gate_tasks = GATE_PRESETS[@gate_preset][:lines].map { |name, days| self.class.line(name, days, EVIDENCE[@evidence_mode]) }
      estimate = {
        "confidence" => "high", "reasoning" => "demo", "modules" => [ { "name" => "Auth", "tasks" => @gate_tasks } ],
        "total_engineer_days" => @gate_tasks.sum { |t| t["engineer_days"].to_f }
      }
      @gate_result = client.verify(estimate: estimate, kept_chunks: [ CHUNK_120H ], use_judge: @use_judge)
      render :show
    rescue EstimatorAi::Error, Faraday::Error => e
      fail_with(e)
    end

    def hours
      @tab = "conflict"
      prepare_defaults
      @task_name = params[:task_name].to_s.strip.presence || HOURS_PRESETS["conflict"][:name]
      @task_description = params[:task_description].to_s.strip
      @task_module = params[:task_module].to_s.strip.presence || "Notifications"
      # The module name is part of the search text: the same task under another
      # module retrieves other neighbours (and can lose the 40 h analog).
      result = client.task_hours(modules: [ { name: @task_module, tasks: [ { name: @task_name, description: @task_description } ] } ])
      @hours_result = Array(result["tasks"]).first
      render :show
    rescue EstimatorAi::Error, Faraday::Error => e
      fail_with(e)
    end

    def augment
      @tab = "augment"
      prepare_defaults
      @augment_query = params[:query_text].to_s.strip.presence || AUGMENT_PRESETS["banking"]
      retrieval = client.retrieve(query_text: @augment_query)
      chunks = Array(retrieval["chunks"])
      if chunks.empty?
        flash.now[:alert] = "La búsqueda no devolvió chunks bajo el umbral."
      else
        @augment_off = client.assemble(chunks: chunks, augment: false)
        @augment_on = client.assemble(chunks: chunks, augment: true)
      end
      render :show
    rescue EstimatorAi::Error, Faraday::Error => e
      fail_with(e)
    end

    def toggles
      @tab = "toggles"
      changes = TOGGLES.keys.index_with do |field|
        case params.dig(:toggles, field)
        when "on" then true
        when "off" then false
        end # "default" → nil → reset to the .env value
      end
      client.update_retrieval_config(changes)
      redirect_to rag_quality_path(tab: "toggles"), notice: "Interruptores actualizados (sin reiniciar nada)."
    rescue EstimatorAi::Error, Faraday::Error => e
      prepare_defaults
      fail_with(e)
    end

    private

    def client
      @client ||= EstimatorAi::QualityClient.new(timeout: 300)
    end

    def prepare_defaults
      @gate_preset ||= "all_four"
      @evidence_mode ||= "full"
      @task_module ||= HOURS_PRESETS["conflict"][:module]
      @task_name ||= HOURS_PRESETS["conflict"][:name]
      @task_description ||= HOURS_PRESETS["conflict"][:description]
      @augment_query ||= AUGMENT_PRESETS["banking"]
    end

    def load_toggles
      @toggles = client.retrieval_config.fetch("retrieval", {})
    rescue EstimatorAi::Error, Faraday::Error => e
      flash.now[:alert] = "No se pudo leer la configuración: #{e.class}"
      @toggles = {}
    end

    def fail_with(error)
      load_toggles if @tab == "toggles"
      flash.now[:alert] = "Error del servicio IA: #{error.message.to_s.truncate(300)}"
      render :show, status: :service_unavailable
    end
  end
end
