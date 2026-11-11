# «Corpus»: what is actually indexed in the AI service, collection by collection
# (budget · transcript · technical_doc), rendered as cards with their metadata.
module Rag
  class CorpusController < ApplicationController
    COLLECTIONS = {
      "budget" => "Presupuestos",
      "transcript" => "Transcripciones",
      "technical_doc" => "Documentación técnica"
    }.freeze
    PER_PAGE = 30

    def index
      @collection = COLLECTIONS.key?(params[:collection]) ? params[:collection] : "budget"
      @chunk_type = params[:chunk_type].presence
      @q = params[:q].to_s.strip
      @page = [ params[:page].to_i, 1 ].max

      client = EstimatorAi::CorpusClient.new
      @summary = client.summary["collections"].index_by { |c| c["collection"] }
      @result = client.chunks(collection: @collection, chunk_type: @chunk_type, q: @q,
                              limit: PER_PAGE, offset: (@page - 1) * PER_PAGE)
      @total_pages = [ (@result["total"].to_f / PER_PAGE).ceil, 1 ].max
    rescue EstimatorAi::Error, Faraday::Error => e
      @error = "No se ha podido leer el corpus del servicio IA: #{e.message}"
      @summary = {}
      @result = { "chunks" => [], "total" => 0 }
      @total_pages = 1
    end
  end
end
