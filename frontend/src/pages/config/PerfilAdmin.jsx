import { useNavigate } from 'react-router-dom'

const PERFIS = [
  {
    papel: 'admin',
    label: 'Administrador',
    cor: 'bg-gray-800 text-white',
    descricao: 'Acesso total ao sistema. Gerencia órgãos, unidades, usuários e todos os parâmetros.',
    permissoes: [
      'Cadastrar e editar órgãos e unidades',
      'Gerenciar usuários e perfis',
      'Configurar parâmetros do sistema',
      'Acesso a todos os módulos e documentos',
      'Aprovar e devolver qualquer documento',
      'Visualizar todos os relatórios e painéis',
    ],
  },
  {
    papel: 'gestor_planejamento',
    label: 'Gestor de Planejamento',
    cor: 'bg-orange-600 text-white',
    descricao: 'Responsável pelo planejamento orçamentário e aprovação de necessidades.',
    permissoes: [
      'Aprovar / rejeitar / bloquear necessidades',
      'Cadastrar e editar plano orçamentário',
      'Vincular necessidades ao plano orçamentário',
      'Cadastrar ações orçamentárias, elementos, naturezas e fontes',
      'Gerenciar dotações e indicações orçamentárias',
      'Visualizar painel consolidado do órgão',
    ],
  },
  {
    papel: 'analista',
    label: 'Analista / Gestor de Contrato',
    cor: 'bg-yellow-600 text-white',
    descricao: 'Analisa e aprova documentos técnicos (DFD, ETP) da fase preparatória.',
    permissoes: [
      'Iniciar análise de DFDs e ETPs',
      'Aprovar DFDs e ETPs',
      'Devolver DFDs e ETPs com motivo',
      'Visualizar todos os documentos do órgão',
    ],
  },
  {
    papel: 'ordenador',
    label: 'Ordenador de Despesa',
    cor: 'bg-indigo-600 text-white',
    descricao: 'Autoriza a indicação orçamentária — emite a Declaração do Ordenador de Despesa (DOD).',
    permissoes: [
      'Aprovar indicações orçamentárias (emitir DOD)',
      'Cancelar indicações orçamentárias',
      'Visualizar dotações e indicações',
      'Baixar DOD em PDF',
    ],
  },
  {
    papel: 'solicitante',
    label: 'Solicitante / Demandante',
    cor: 'bg-purple-600 text-white',
    descricao: 'Unidade demandante — cria e gerencia as necessidades e documentos técnicos.',
    permissoes: [
      'Cadastrar necessidades de planejamento',
      'Criar DFDs a partir de necessidades aprovadas',
      'Criar ETPs a partir de DFDs aprovados',
      'Criar Minutas TR a partir de ETPs aprovados',
      'Corrigir e resubmeter documentos devolvidos',
      'Exportar DFD, ETP e Minuta TR em PDF/HTML',
    ],
  },
  {
    papel: 'gestor_contrato',
    label: 'Gestor de Contrato',
    cor: 'bg-teal-600 text-white',
    descricao: 'Acompanha a execução contratual.',
    permissoes: [
      'Visualizar DFDs, ETPs e TRs do órgão',
      'Acompanhar status dos contratos',
    ],
  },
  {
    papel: 'fiscal_contrato',
    label: 'Fiscal de Contrato',
    cor: 'bg-cyan-600 text-white',
    descricao: 'Fiscaliza a execução dos contratos.',
    permissoes: [
      'Visualizar documentos da fase de contratação',
      'Registrar ocorrências de fiscalização',
    ],
  },
]

const TIPOS_UNIDADE = [
  {
    tipo: 'demandante',
    label: 'Unidade Demandante',
    cor: 'bg-purple-100 text-purple-800',
    descricao: 'Identifica e formaliza as necessidades. Ex: CMP, CORSEG, unidades da PMBA/CBMBA.',
  },
  {
    tipo: 'licitante',
    label: 'Unidade Licitante',
    cor: 'bg-blue-100 text-blue-800',
    descricao: 'Conduz o processo licitatório. Ex: CLIC. Acessa parâmetros de licitação e pode configurar limite de dispensa de ETP.',
  },
  {
    tipo: 'contratante',
    label: 'Unidade Contratante',
    cor: 'bg-green-100 text-green-800',
    descricao: 'Gerencia os contratos celebrados. Ex: CCC.',
  },
  {
    tipo: 'planejamento',
    label: 'Unidade de Planejamento',
    cor: 'bg-orange-100 text-orange-800',
    descricao: 'Coordena o planejamento orçamentário. Ex: DG, CPLAM, CFCR, DEPLAN. Acessa tabelas orçamentárias e parâmetros do sistema.',
  },
]

export default function PerfilAdmin() {
  const navigate = useNavigate()

  return (
    <div className="p-6 lg:p-8 max-w-4xl">
      <div className="mb-8">
        <h1 className="text-xl font-bold text-gray-800">Perfis e Permissões</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Visão geral do que cada perfil pode fazer no sistema.
          Para alterar o perfil de um usuário, acesse{' '}
          <button onClick={() => navigate('/config/usuarios')}
            className="text-blue-600 hover:underline font-medium">
            Gerenciar Usuários
          </button>.
        </p>
      </div>

      {/* Perfis de Papel */}
      <section className="mb-10">
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">Papéis do Sistema</h2>
        <div className="space-y-4">
          {PERFIS.map((p) => (
            <div key={p.papel} className="bg-white border border-gray-200 rounded-xl overflow-hidden">
              <div className={`px-5 py-3 flex items-center gap-3 ${p.cor}`}>
                <span className="font-semibold text-sm">{p.label}</span>
                <span className="text-xs opacity-75 font-mono">({p.papel})</span>
              </div>
              <div className="px-5 py-4">
                <p className="text-sm text-gray-600 mb-3">{p.descricao}</p>
                <ul className="space-y-1">
                  {p.permissoes.map((perm, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                      <span className="text-green-500 mt-0.5 shrink-0">✓</span>
                      {perm}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Tipos de Unidade */}
      <section>
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">Tipos de Unidade Organizacional</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {TIPOS_UNIDADE.map((u) => (
            <div key={u.tipo} className="bg-white border border-gray-200 rounded-xl p-5">
              <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-semibold mb-2 ${u.cor}`}>
                {u.label}
              </span>
              <p className="text-sm text-gray-600">{u.descricao}</p>
            </div>
          ))}
        </div>
        <div className="mt-4 bg-blue-50 border border-blue-200 rounded-xl p-4 text-sm text-blue-800">
          <strong>Como funciona:</strong> O acesso de um usuário é determinado pela combinação de seu <em>papel</em> (ex: gestor_planejamento) e o <em>tipo da unidade</em> à qual está vinculado (ex: planejamento). Isso permite controle granular: um gestor_planejamento na unidade licitante tem acesso diferente de um na unidade de planejamento.
        </div>
      </section>
    </div>
  )
}
