// ─── Ajuda Contextual ────────────────────────────────────────────────────────
export const pageHelp = {
  titulo: 'Central de Ajuda',
  descricao: 'Referência estática sobre a hierarquia de órgãos, perfis de usuário e o fluxo completo de contratação do sistema — complementa a ajuda contextual (botão "?") disponível em cada tela.',
}
// ──────────────────────────────────────────────────────────────────────────────

export default function Ajuda() {
  return (
    <div className="p-8 max-w-3xl">
      <h1 className="text-2xl font-bold text-gray-800 mb-2">Central de Ajuda — WEBER-E</h1>
      <p className="text-sm text-gray-500 mb-8">
        Orientações sobre fluxos, ações disponíveis e regras de negócio do sistema.
        Baseado na Lei 14.133/2021 e Decreto Estadual 22.886/2024.
      </p>

      <div className="space-y-8">

        <Section title="Hierarquia de Órgãos">
          <p>O sistema suporta hierarquia de órgãos pai/filho.</p>
          <ul className="list-disc ml-5 space-y-1 mt-2">
            <li><strong>Órgão Pai (ex: SSP)</strong> — centraliza licitações e visualiza demandas de todos os filhos.</li>
            <li><strong>Órgãos Filhos (ex: PMBA, CBMBA)</strong> — criam necessidades que podem ser executadas internamente ou repassadas ao pai.</li>
          </ul>
        </Section>

        <Section title="Perfis de Usuário">
          <table className="w-full text-sm border border-gray-200 rounded-lg overflow-hidden">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-4 py-2 font-medium text-gray-500">Perfil</th>
                <th className="text-left px-4 py-2 font-medium text-gray-500">Responsabilidade principal</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {[
                ['Solicitante / Demandante', 'Cadastra necessidades, cria DFD, ETP e Minuta TR'],
                ['Gestor de Planejamento', 'Aprova necessidades, gerencia plano orçamentário e dotações'],
                ['Analista', 'Analisa, aprova e devolve DFDs e ETPs'],
                ['Ordenador de Despesa', 'Aprova indicações orçamentárias (emite DOD)'],
                ['Licitante', 'Conduz licitações e configura parâmetros do sistema'],
                ['Administrador', 'Acesso total, gestão de órgãos, usuários e parâmetros'],
              ].map(([papel, desc]) => (
                <tr key={papel} className="hover:bg-gray-50">
                  <td className="px-4 py-2 font-medium text-gray-700 whitespace-nowrap">{papel}</td>
                  <td className="px-4 py-2 text-gray-600">{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <Info>Acesse <strong>Configurações → Perfis e Permissões</strong> para ver o detalhamento completo de cada perfil.</Info>
        </Section>

        <Section title="Fluxo Completo de Contratação">
          <ol className="space-y-2 mt-2">
            {[
              { n: '1', label: 'Necessidade', desc: 'Demandante identifica e cadastra a necessidade com tipo de execução.' },
              { n: '2', label: 'Plano Orçamentário', desc: 'Planejamento vincula a necessidade ao plano orçamentário e às dotações.' },
              { n: '3', label: 'DFD', desc: 'Demandante formaliza a demanda com itens, valores e modalidade.' },
              { n: '4', label: 'ETP', desc: 'Demandante elabora o Estudo Técnico Preliminar (pode ser dispensado).' },
              { n: '5', label: 'Indicação / DOD', desc: 'Planejamento indica os recursos e o Ordenador emite a DOD.' },
              { n: '6', label: 'Minuta TR', desc: 'Demandante elabora a Minuta do Termo de Referência.' },
              { n: '7', label: 'Licitação', desc: 'Documentos exportados para o SEI e processo licitatório iniciado.' },
            ].map(({ n, label, desc }) => (
              <li key={n} className="flex gap-3 items-start">
                <span className="shrink-0 w-6 h-6 rounded-full bg-blue-600 text-white text-xs font-bold flex items-center justify-center mt-0.5">{n}</span>
                <div>
                  <span className="font-semibold text-gray-800">{label}</span>
                  <span className="text-gray-600"> — {desc}</span>
                </div>
              </li>
            ))}
          </ol>
        </Section>

        <Section title="Fluxo da Necessidade de Planejamento">
          <Flow steps={[
            { status: 'Identificada', desc: 'Demandante cadastra com tipo de execução (interna ou externa).' },
            { status: 'Em Análise', desc: 'Unidade de Planejamento analisa.' },
            { status: 'Aprovada', desc: 'Planejamento aprova. A necessidade pode originar um DFD.' },
            { status: 'DFD Criado', desc: 'DFD foi gerado e vinculado a esta necessidade.' },
            { status: 'Cancelada', desc: 'Planejamento bloqueou (sem orçamento ou planejamento inadequado).' },
          ]} />
          <Info>Para necessidades com <strong>Execução Externa</strong>, o órgão pai visualiza na fila de aceite e pode aceitar ou recusar em lote.</Info>
        </Section>

        <Section title="Fluxo do DFD">
          <Flow steps={[
            { status: 'Rascunho', desc: 'Demandante cria o DFD, vincula à necessidade aprovada e preenche itens.' },
            { status: 'Submetida', desc: 'DFD submetido para análise da unidade licitante.' },
            { status: 'Em Análise', desc: 'Analista iniciou análise. Órgão de compras é registrado.' },
            { status: 'Aprovada', desc: 'DFD aprovado. Habilita a criação do ETP.' },
            { status: 'Devolvida', desc: 'DFD devolvido com motivo. Demandante corrige e resubmete.' },
          ]} />
        </Section>

        <Section title="Fluxo do ETP">
          <Flow steps={[
            { status: 'Rascunho', desc: 'Demandante cria o ETP a partir de um DFD aprovado.' },
            { status: 'Submetido', desc: 'ETP submetido para análise.' },
            { status: 'Em Análise', desc: 'Analista iniciou análise do ETP.' },
            { status: 'Aprovado', desc: 'ETP aprovado. Habilita a Minuta TR.' },
            { status: 'Devolvido', desc: 'ETP devolvido com motivo.' },
            { status: 'Dispensado', desc: 'ETP dispensado automaticamente (contratação direta ≤ limite ou ARP).' },
          ]} />
          <Info>O limite de dispensa de ETP é configurável em <strong>Configurações → Parâmetros do Sistema</strong> (padrão: R$ 62.000 — art. 75, Lei 14.133/2021).</Info>
        </Section>

        <Section title="Fluxo da Indicação Orçamentária / DOD">
          <Flow steps={[
            { status: 'Rascunho', desc: 'Planejamento cria a indicação e vincula uma ou mais dotações com valores específicos.' },
            { status: 'Submetida', desc: 'Indicação submetida ao Ordenador de Despesa para aprovação.' },
            { status: 'Aprovada', desc: 'Ordenador aprova — DOD gerada. PDF disponível para download.' },
            { status: 'Cancelada', desc: 'Indicação cancelada com motivo registrado no histórico.' },
          ]} />
          <Info>A DOD pode ter uma ou mais dotações. Ao aprovar, o sistema atualiza automaticamente o <strong>valor indicado</strong> em cada dotação vinculada.</Info>
        </Section>

        <Section title="Fluxo da Minuta do Termo de Referência">
          <Flow steps={[
            { status: 'Rascunho', desc: 'Demandante elabora a Minuta TR a partir de um ETP aprovado.' },
            { status: 'Submetido', desc: 'Minuta submetida para análise.' },
            { status: 'Em Análise', desc: 'Analista analisa a Minuta TR.' },
            { status: 'Aprovado', desc: 'Minuta TR aprovada. Disponível para exportação em PDF/HTML para o SEI.' },
            { status: 'Devolvido', desc: 'Devolvido para ajuste com motivo.' },
          ]} />
        </Section>

        <Section title="Autenticidade dos Documentos">
          <ul className="list-disc ml-5 space-y-2 text-sm text-gray-700">
            <li>Todos os documentos gerados (DFD, ETP, Minuta TR, DOD) incluem um <strong>Código de Verificação</strong> no rodapé.</li>
            <li>O código pode ser validado no endpoint <code className="bg-gray-100 px-1 rounded text-xs">/api/verificar/&lt;código&gt;/</code>.</li>
            <li>O SEI pode utilizar o código para validar o documento como <strong>externo autenticado</strong>.</li>
            <li>O código inclui dados do criador, aprovador, órgão e timestamps — garantindo rastreabilidade.</li>
          </ul>
        </Section>

        <Section title="Regras de Negócio Importantes">
          <ul className="list-disc ml-5 space-y-2 text-sm text-gray-700">
            <li>Necessidade com <strong>execução externa</strong> vai para fila de aceite do órgão pai.</li>
            <li>DFD não pode ser submetido sem necessidade em plano orçamentário (exige justificativa).</li>
            <li>DFD não pode ser submetido com valor acima de <strong>{'{percentual}'}%</strong> do planejado sem justificativa.</li>
            <li>ETP dispensado automaticamente para contratações diretas abaixo do limite configurável.</li>
            <li>A Natureza de Despesa (ex: 3.3.90.30) define automaticamente o Elemento (ex: 30).</li>
            <li>Indicação orçamentária com múltiplas dotações — valor indicado de cada dotação é registrado separadamente.</li>
            <li>Todos os documentos têm histórico imutável de tramitações com usuário, data e motivo.</li>
          </ul>
        </Section>

      </div>
    </div>
  )
}

function Section({ title, children }) {
  return (
    <div>
      <h2 className="text-base font-semibold text-gray-800 border-b border-gray-200 pb-2 mb-3">{title}</h2>
      <div className="text-sm text-gray-700 space-y-2">{children}</div>
    </div>
  )
}

function Info({ children }) {
  return (
    <div className="mt-3 bg-blue-50 border border-blue-200 rounded-lg px-4 py-3 text-sm text-blue-800">
      {children}
    </div>
  )
}

const STATUS_CLS = {
  Identificada: 'bg-gray-100 text-gray-600',
  'Em Análise': 'bg-yellow-100 text-yellow-700',
  Aprovada:     'bg-green-100 text-green-700',
  'DFD Criado': 'bg-blue-100 text-blue-700',
  Cancelada:    'bg-red-100 text-red-700',
  Rascunho:     'bg-gray-100 text-gray-600',
  Submetida:    'bg-blue-100 text-blue-700',
  Submetido:    'bg-blue-100 text-blue-700',
  Devolvida:    'bg-orange-100 text-orange-700',
  Devolvido:    'bg-orange-100 text-orange-700',
  Rejeitada:    'bg-red-100 text-red-700',
  Aprovado:     'bg-green-100 text-green-700',
  Dispensado:   'bg-purple-100 text-purple-700',
}

function Flow({ steps }) {
  return (
    <ol className="space-y-3 mt-2">
      {steps.map((s, i) => (
        <li key={i} className="flex items-start gap-3">
          <span className={`shrink-0 mt-0.5 px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_CLS[s.status] || 'bg-gray-100 text-gray-600'}`}>
            {s.status}
          </span>
          <span className="text-sm text-gray-700">{s.desc}</span>
        </li>
      ))}
    </ol>
  )
}
