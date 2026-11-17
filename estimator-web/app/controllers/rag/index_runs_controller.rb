# Corpus / Índice (Session 11): add NEW information to the vector DB and watch it
# get indexed. Unlike the Chunking Lab (synchronous), expansion is an async job
# in the IA service: create → POST 202 + job_id, then the show page POLLS the
# `status` member action until the job finishes and the corpus stats grow.
module Rag
  class IndexRunsController < ApplicationController
    EXPAND_TIMEOUT_SECONDS = 120

    def index
      @runs = Rag::IndexRun.order(created_at: :desc).limit(20)
      @stats = fetch_stats
    rescue EstimatorAi::Error, Faraday::Error => e
      @runs ||= Rag::IndexRun.order(created_at: :desc).limit(20)
      @stats = nil
      flash.now[:alert] = "No se pudieron leer las estadísticas del corpus: #{e.class}"
    end

    def new
      @chunk_type = "budget_component"
      @documents_json = EXAMPLE_JSON
    end

    def create
      @chunk_type = params[:chunk_type].presence || "budget_component"
      @documents_json = params[:documents_json].to_s
      documents = parse_documents(@documents_json)

      if documents.blank?
        flash.now[:alert] = "Pega al menos un documento (objeto JSON o array de objetos)."
        return render :new, status: :unprocessable_entity
      end

      before = fetch_stats
      response = client.start_expansion(documents: documents, chunk_type: @chunk_type)
      run = Rag::IndexRun.create!(
        job_id: response["job_id"],
        chunk_type: @chunk_type,
        submitted_count: response["documents_total"].to_i,
        status: response["status"].presence || "pending",
        before_stats: before || {}
      )
      redirect_to rag_index_run_path(run)
    rescue JSON::ParserError => e
      flash.now[:alert] = "JSON inválido: #{e.message}"
      render :new, status: :unprocessable_entity
    rescue EstimatorAi::IndexClient::InvalidBatch => e
      flash.now[:alert] = "El servicio IA rechazó el lote (¿faltan campos del presupuesto?): #{e.message}"
      render :new, status: :unprocessable_entity
    rescue EstimatorAi::Error => e
      flash.now[:alert] = "Error del servicio IA: #{e.message}"
      render :new, status: :service_unavailable
    rescue Faraday::TimeoutError, Faraday::ConnectionFailed => e
      flash.now[:alert] = "El servicio IA no respondió a tiempo. (#{e.class})"
      render :new, status: :service_unavailable
    end

    def show
      @run = Rag::IndexRun.find(params[:id])
    end

    # Polled by the show page (JSON). Refreshes the job snapshot and, once the job
    # finishes, captures the grown corpus stats so the UI shows the delta.
    def status
      @run = Rag::IndexRun.find(params[:id])
      unless @run.finished?
        snapshot = client.job_status(@run.job_id)
        attrs = { status: snapshot["status"], documents_processed: snapshot["documents_processed"].to_i }
        attrs[:after_stats] = fetch_stats || {} if Rag::IndexRun::TERMINAL_STATUSES.include?(snapshot["status"])
        @run.update!(attrs)
      end
      render json: {
        status: @run.status,
        finished: @run.finished?,
        documents_processed: @run.documents_processed,
        submitted_count: @run.submitted_count,
        chunks_added: @run.chunks_added
      }
    rescue EstimatorAi::Error, Faraday::Error => e
      render json: { status: @run&.status || "unknown", finished: false, error: e.class.to_s }, status: :ok
    end

    private

    def client
      EstimatorAi::IndexClient.new(timeout: EXPAND_TIMEOUT_SECONDS)
    end

    def fetch_stats
      client.corpus_stats
    end

    # Accept either a single budget object or an array of them.
    def parse_documents(text)
      parsed = JSON.parse(text)
      parsed.is_a?(Array) ? parsed : [ parsed ]
    end

    # Local (S11 class): a project the corpus has NOTHING like, so the growth is
    # visible in retrieval too — before indexing, "biometric KYC onboarding" only
    # finds generic finance tasks (~0.47); after, its three chunks lead (~0.17).
    EXAMPLE_JSON = <<~JSON.freeze
      {
        "budget_id": "BUD-2025-0100",
        "client_metadata": { "name": "Neobanco Demo", "sector": "finance", "country": "ES" },
        "project_summary": "Biometric KYC onboarding for a neobank: identity document OCR, selfie liveness detection and AML screening",
        "main_technology": "Python",
        "year": 2025,
        "total_estimated_hours": 300,
        "components": [
          { "component_id": "KYC-001", "name": "Identity document OCR",
            "description": "Capture and OCR of ID cards and passports with MRZ validation and fraud checks",
            "module": "Onboarding & KYC", "tech_stack": ["Python", "AWS Textract"], "estimated_hours": 110,
            "complexity": "high", "dependencies": [] },
          { "component_id": "KYC-002", "name": "Selfie liveness detection",
            "description": "Passive and active liveness detection with face match against the ID photo",
            "module": "Onboarding & KYC", "tech_stack": ["Python"], "estimated_hours": 120,
            "complexity": "high", "dependencies": ["KYC-001"] },
          { "component_id": "KYC-003", "name": "AML and sanctions screening",
            "description": "Screening against sanctions and PEP lists with a manual review queue",
            "module": "Compliance", "tech_stack": ["Python", "PostgreSQL"], "estimated_hours": 70,
            "complexity": "medium", "dependencies": ["KYC-001"] }
        ]
      }
    JSON
  end
end
