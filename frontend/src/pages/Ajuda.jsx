export default function Ajuda() {
  return (
    <div className="p-8 max-w-3xl">
      <h1 className="text-2xl font-bold text-gray-800 mb-2">Central de Ajuda — WEBBER</h1>
      <p className="text-sm text-gray-500 mb-8">
        Orientações sobre fluxos, ações disponíveis e regras de negócio do sistema.
      </p>

      <div className="space-y-8">

        {/* Hierarquia de Órgãos */}
        <Section title="Hierarquia de Órgãos">
          <p>O sistema suporta uma hierarquia de órgãos pai/filho.</p>
          <ul className="list-disc ml-5 space-y-1 mt-2">
            <li><strong>Órgão Pai (ex: SSP)</strong> — centraliza licitações e visualiza demandas de todos os filhos.</li>
            <li><strong>Órgãos Filhos (ex: PMBA, CBMBA)</strong> — criam necessidades que podem ser executadas internamente ou repassadas ao pai.</li>
          </ul>
        </Section>

        {/* Perfis e Permissões */}
        <Section title="Perfis de Usuário e Permissões">
          <table className="w-full text-sm border border-gray-200 rounded-lg overflow-hidden">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-4 py-2 font-medium text-gray-500">Perfil</th>
                <th className="text-left px-4 py-2 font-medium text-gray-500">Pode fazer</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {[
                ['Solicitante / Demandante', 'Cadastrar necessidades, submeter e corrigir DFDs e ETPs devolvidos'],
                ['Gestor de Planejamento', 'Aprovar/rejeitar necessidades, cadastrar e editar Plano Orçamentário, vincular demandas, bloquear necessidades sem plano'],
                ['Analista / Gestor de Contrato', 'Iniciar análise, aprovar e devolver DFDs e ETPs'],
                ['Ordenador', 'Aprovar dotações e DFDs'],
                ['Administrador', 'Acesso total + gestão de órgãos, unidades e usuários'],
              ].map(([papel, desc]) => (
                <tr key={papel} className="hover:bg-gray-50">
                  <td className="px-4 py-2 font-medium text-gray-700 whitespace-nowrap">{papel}</td>
                  <td className="px-4 py-2 text-gray-600">{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Section>

        {/* Fluxo de Necessidade */}
        <Section title="Fluxo da Necessidade de Planejamento">
          <Flow steps={[
            { status: 'Identificada', desc: 'Demandante cadastra a necessidade com tipo de execução (interna ou externa ao órgão).' },
            { status: 'Em Análise', desc: 'Unidade de Planejamento analisa e pode solicitar ajustes.' },
            { status: 'Aprovada', desc: 'Planejamento aprova. A necessidade pode agora originar um DFD.' },
            { status: 'DFD Criado', desc: 'Demandante criou o DFD vinculado a esta necessidade.' },
            { status: 'Cancelada', desc: 'Planejamento bloqueou a necessidade (sem orçamento ou planejamento inadequado).' },
          ]} />
          <Info>Para necessidades com <strong>Execução Externa</strong>, o sistema automaticamente vincula ao órgão pai e exibe a necessidade no painel da SSP com badge "Herdada".</Info>
        </Section>

        {/* Plano Orçamentário */}
        <Section title="Plano Orçamentário">
          <ul className="list-disc ml-5 space-y-1 text-sm text-gray-700">
            <li>Criado pela <strong>Unidade de Planejamento</strong> do órgão.</li>
            <li>Vincula necessidades com classificação de origem: <em>Demanda Própria</em> ou <em>Demanda de Órgão Filho</em>.</li>
            <li>Uma necessidade sem plano orçamentário vinculado bloqueia a submissão do DFD (a menos que haja justificativa).</li>
            <li>A dotação total do plano é comparada com a soma dos valores das necessidades vinculadas.</li>
          </ul>
        </Section>

        {/* Fluxo DFD */}
        <Section title="Fluxo do DFD (Documento de Formalização de Demanda)">
          <Flow steps={[
            { status: 'Rascunho', desc: 'Demandante cria o DFD, vincula à necessidade aprovada e preenche itens.' },
            { status: 'Submetida', desc: 'DFD submetido para análise da unidade licitante.' },
            { status: 'Em Análise', desc: 'Analista iniciou análise. Órgão de compras é registrado.' },
            { status: 'Aprovada', desc: 'DFD aprovado. Habilita a criação do ETP.' },
            { status: 'Devolvida', desc: 'DFD devolvido ao demandante para ajuste (motivo registrado no histórico).' },
            { status: 'Rejeitada', desc: 'DFD rejeitado definitivamente.' },
          ]} />
          <Info>O <strong>número SEI do DFD</strong> é pre-preenchido no ETP ao criá-lo, mas pode ser alterado — o histórico de alterações é mantido.</Info>
        </Section>

        {/* Fluxo ETP */}
        <Section title="Fluxo do ETP (Estudo Técnico Preliminar)">
          <Flow steps={[
            { status: 'Rascunho', desc: 'Demandante cria o ETP a partir de um DFD aprovado e preenche as seções.' },
            { status: 'Submetido', desc: 'ETP submetido para análise.' },
            { status: 'Em Análise', desc: 'Analista iniciou análise do ETP.' },
            { status: 'Aprovado', desc: 'ETP aprovado. Habilita a elaboração do Termo de Referência.' },
            { status: 'Devolvido', desc: 'ETP devolvido para ajuste (motivo registrado no histórico).' },
          ]} />
        </Section>

        {/* Regras de Negócio */}
        <Section title="Regras de Negócio Importantes">
          <ul className="list-disc ml-5 space-y-2 text-sm text-gray-700">
            <li>Necessidade com <strong>tipo_execucao = externa</strong> é automaticamente vinculada ao órgão pai como executor.</li>
            <li>O DFD não pode ser submetido se a necessidade não estiver em um plano orçamentário (exige justificativa).</li>
            <li>O DFD não pode ser submetido se o valor extrapolar em mais de 10% o planejado (exige justificativa).</li>
            <li>O ETP só pode ser criado para DFDs com status <strong>Aprovada</strong>.</li>
            <li>Cada DFD pode ter apenas um ETP.</li>
            <li>Motivos de devolução ficam registrados no histórico de tramitação de DFDs e ETPs.</li>
            <li>Alterações no número SEI do ETP geram histórico rastreável com motivo.</li>
          </ul>
        </Section>

        {/* Painel Órgão Pai */}
        <Section title="Painel do Órgão Pai">
          <p className="text-sm text-gray-700">
            Disponível no menu <strong>Painel</strong>, exibe todas as necessidades, DFDs e ETPs
            organizados por órgão e unidade demandante. Necessidades herdadas de órgãos filhos
            aparecem com badge <span className="inline-block px-1.5 py-0.5 rounded text-xs bg-indigo-100 text-indigo-700 font-medium">Herdada</span>.
          </p>
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
