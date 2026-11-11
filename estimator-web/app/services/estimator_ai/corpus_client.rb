# Read-only view of the indexed corpus (GET /api/v1/corpus): totals per
# collection and paginated chunks with their metadata, for the «Corpus» view.
module EstimatorAi
  class CorpusClient < BaseClient
    def summary
      handle_response(json_conn.get("/api/v1/corpus"))
    end

    def chunks(collection:, chunk_type: nil, q: nil, limit: 30, offset: 0)
      params = { chunk_type: chunk_type.presence, q: q.presence, limit: limit, offset: offset }.compact
      handle_response(json_conn.get("/api/v1/corpus/#{collection}", params))
    end
  end
end
