# «Histórico»: every persisted run of the app in one timeline — advanced
# searches (S10), wizard estimations (S9/S10) and chunking comparisons (S7).
class HistoryController < ApplicationController
  Item = Struct.new(:kind, :label, :title, :detail, :created_at, :path, keyword_init: true)

  def index
    @kind = params[:kind].presence
    items = []
    if @kind.nil? || @kind == "search"
      items += Rag::AdvancedSearch.order(created_at: :desc).limit(100).map do |s|
        Item.new(kind: "search", label: "Búsqueda", title: s.query_text,
                 detail: "#{s.routing['level'] || '—'} → #{Array(s.routing['targets']).join(', ')} · #{s.technique} · " \
                         "#{s.chunks.size} resultados · #{s.duration_seconds} s",
                 created_at: s.created_at, path: rag_advanced_search_path(s))
      end
    end
    if @kind.nil? || @kind == "estimation"
      items += Rag::EstimationRun.order(created_at: :desc).limit(100).map do |r|
        Item.new(kind: "estimation", label: "Estimación", title: r.transcript.to_s.truncate(110),
                 detail: "paso: #{r.current_step} · #{r.confirmed? ? 'confirmada' : r.status}",
                 created_at: r.created_at, path: rag_estimation_run_path(r))
      end
    end
    if @kind.nil? || @kind == "chunking"
      items += Rag::ChunkingComparison.order(created_at: :desc).limit(100).map do |c|
        Item.new(kind: "chunking", label: "Chunking Lab", title: c.strategy_labels.join(" · "),
                 detail: "#{c.queries.size} consultas · #{c.duration_seconds} s",
                 created_at: c.created_at, path: rag_chunking_comparison_path(c))
      end
    end
    @items = items.sort_by(&:created_at).reverse
  end
end
