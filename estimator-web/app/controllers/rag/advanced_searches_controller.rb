# «Búsqueda» (Session 10): runs the advanced retrieval pipeline from the UI
# (POST /v1/retrieval/advanced-search) and persists each run, so the live demos
# of routing, expansion/decomposition and hard filters can be shown on screen
# and revisited from the history.
module Rag
  class AdvancedSearchesController < ApplicationController
    COLLECTIONS = %w[budget transcript technical_doc].freeze
    TOGGLES = %w[routing_enabled query_transform_enabled rerank temporal_decay_enabled].freeze

    # The demos of the session guide, one click away.
    PRESETS = {
      "reglas" => { label: "Routing · reglas",
                    query_text: "what did the client say in the meeting about Stripe checkout" },
      "clasificador" => { label: "Routing · clasificador LLM",
                          query_text: "OAuth 2.0 PKCE flow and PSD2 strong customer authentication reference" },
      "explicito" => { label: "Routing · explícito",
                       query_text: "telemedicine appointment scheduling", collections: %w[budget] },
      "descomposicion" => { label: "Descomposición",
                            query_text: "we need OAuth and a transaction ledger, plus a Stripe checkout, and also " \
                                        "personalized recommendations for the product catalog",
                            collections: %w[budget], top_k: 5 },
      "directa" => { label: "Consulta directa", query_text: "Stripe checkout", collections: %w[budget] },
      "filtro" => { label: "Filtro por fecha",
                    query_text: "telemedicine scheduling and video consultations",
                    collections: %w[budget], min_date: "2024-01-01" },
      "decaimiento" => { label: "Rerank + decaimiento",
                         query_text: "SAP integration with IDoc BAPI for predictive maintenance",
                         toggles: { "rerank" => "true", "temporal_decay_enabled" => "true" }, top_k: 4 }
    }.freeze

    def index
      @searches = Rag::AdvancedSearch.order(created_at: :desc).limit(50)
    end

    def new
      preset = PRESETS[params[:preset]] || {}
      @form = {
        query_text: preset[:query_text].to_s,
        collections: preset[:collections] || [],
        top_k: preset[:top_k] || 3,
        min_date: preset[:min_date].to_s,
        sectors: "",
        toggles: preset[:toggles] || {}
      }
    end

    def create
      @form = form_from_params
      if @form[:query_text].length < 10
        flash.now[:alert] = "La consulta debe tener al menos 10 caracteres."
        return render :new, status: :unprocessable_entity
      end

      request_params = build_request(@form)
      started = Process.clock_gettime(Process::CLOCK_MONOTONIC)
      payload = EstimatorAi::RetrievalClient.new.advanced_search(request_params)
      duration_ms = ((Process.clock_gettime(Process::CLOCK_MONOTONIC) - started) * 1000).round

      search = Rag::AdvancedSearch.create!(
        query_text: @form[:query_text], request_params: request_params,
        response_payload: payload, duration_ms: duration_ms
      )
      redirect_to rag_advanced_search_path(search)
    rescue EstimatorAi::InvalidRequest => e
      flash.now[:alert] = "Petición inválida: #{e.message}"
      render :new, status: :unprocessable_entity
    rescue EstimatorAi::Error, Faraday::Error => e
      flash.now[:alert] = "El servicio IA no ha podido responder: #{e.message} " \
                          "(¿coincide RETRIEVAL_API_KEY con la del servicio IA?)"
      render :new, status: :service_unavailable
    end

    def show
      @search = Rag::AdvancedSearch.find(params[:id])
    end

    private

    def form_from_params
      {
        query_text: params[:query_text].to_s.strip,
        collections: Array(params[:collections]) & COLLECTIONS,
        top_k: params[:top_k].to_i.clamp(1, 30),
        min_date: params[:min_date].to_s.strip,
        sectors: params[:sectors].to_s.strip,
        toggles: params.fetch(:toggles, {}).permit(*TOGGLES).to_h
      }
    end

    # Toggle values: "" = service default (runtime override → .env), "true"/"false" = forced.
    def build_request(form)
      request = {
        query_text: form[:query_text],
        top_k: form[:top_k],
        collections: form[:collections].presence,
        min_date: form[:min_date].presence,
        sectors: form[:sectors].split(",").map(&:strip).compact_blank.presence
      }
      TOGGLES.each do |toggle|
        value = form[:toggles][toggle]
        request[toggle.to_sym] = (value == "true") if %w[true false].include?(value)
      end
      request.compact
    end
  end
end
