// ── Paleta de cores por seção (cards escuros) ─────────────────────────────────
export const MODULE_COLORS = {
  slate:   { bg: 'bg-slate-900',   border: 'border-slate-700',   hover: 'hover:border-slate-500',   iconBg: 'bg-slate-700',   iconText: 'text-slate-200',   text: 'text-slate-100',  accent: 'text-slate-400'   },
  emerald: { bg: 'bg-emerald-950', border: 'border-emerald-800', hover: 'hover:border-emerald-600', iconBg: 'bg-emerald-800', iconText: 'text-emerald-200', text: 'text-emerald-50', accent: 'text-emerald-400'  },
  amber:   { bg: 'bg-amber-950',   border: 'border-amber-800',   hover: 'hover:border-amber-600',   iconBg: 'bg-amber-800',   iconText: 'text-amber-200',   text: 'text-amber-50',   accent: 'text-amber-400'   },
  yellow:  { bg: 'bg-yellow-950',  border: 'border-yellow-800',  hover: 'hover:border-yellow-600',  iconBg: 'bg-yellow-800',  iconText: 'text-yellow-200',  text: 'text-yellow-50',  accent: 'text-yellow-400'  },
  blue:    { bg: 'bg-blue-950',    border: 'border-blue-800',    hover: 'hover:border-blue-600',    iconBg: 'bg-blue-800',    iconText: 'text-blue-200',    text: 'text-blue-50',    accent: 'text-blue-400'    },
  violet:  { bg: 'bg-violet-950',  border: 'border-violet-800',  hover: 'hover:border-violet-600',  iconBg: 'bg-violet-800',  iconText: 'text-violet-200',  text: 'text-violet-50',  accent: 'text-violet-400'  },
  indigo:  { bg: 'bg-indigo-950',  border: 'border-indigo-800',  hover: 'hover:border-indigo-600',  iconBg: 'bg-indigo-800',  iconText: 'text-indigo-200',  text: 'text-indigo-50',  accent: 'text-indigo-400'  },
  orange:  { bg: 'bg-orange-950',  border: 'border-orange-800',  hover: 'hover:border-orange-600',  iconBg: 'bg-orange-800',  iconText: 'text-orange-200',  text: 'text-orange-50',  accent: 'text-orange-400'  },
  teal:    { bg: 'bg-teal-950',    border: 'border-teal-800',    hover: 'hover:border-teal-600',    iconBg: 'bg-teal-800',    iconText: 'text-teal-200',    text: 'text-teal-50',    accent: 'text-teal-400'    },
  sky:     { bg: 'bg-sky-950',     border: 'border-sky-800',     hover: 'hover:border-sky-600',     iconBg: 'bg-sky-800',     iconText: 'text-sky-200',     text: 'text-sky-50',     accent: 'text-sky-400'     },
  gray:    { bg: 'bg-gray-900',    border: 'border-gray-700',    hover: 'hover:border-gray-500',    iconBg: 'bg-gray-700',    iconText: 'text-gray-200',    text: 'text-gray-100',   accent: 'text-gray-400'    },
}

// ── Ícones SVG (heroicons-style, 24×24) ───────────────────────────────────────
const icons = {
  painel: (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
      <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6A2.25 2.25 0 0 1 6 3.75h2.25A2.25 2.25 0 0 1 10.5 6v2.25a2.25 2.25 0 0 1-2.25 2.25H6a2.25 2.25 0 0 1-2.25-2.25V6ZM3.75 15.75A2.25 2.25 0 0 1 6 13.5h2.25a2.25 2.25 0 0 1 2.25 2.25V18a2.25 2.25 0 0 1-2.25 2.25H6A2.25 2.25 0 0 1 3.75 18v-2.25ZM13.5 6a2.25 2.25 0 0 1 2.25-2.25H18A2.25 2.25 0 0 1 20.25 6v2.25A2.25 2.25 0 0 1 18 10.5h-2.25a2.25 2.25 0 0 1-2.25-2.25V6ZM13.5 15.75a2.25 2.25 0 0 1 2.25-2.25H18a2.25 2.25 0 0 1 2.25 2.25V18A2.25 2.25 0 0 1 18 20.25h-2.25A2.25 2.25 0 0 1 13.5 18v-2.25Z" />
    </svg>
  ),
  plano_compras: (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" />
    </svg>
  ),
  necessidades: (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 0 0 2.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 0 0-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 0 0 .75-.75 2.25 2.25 0 0 0-.1-.664m-5.8 0A2.251 2.251 0 0 1 13.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25Z" />
    </svg>
  ),
  aceite: (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12c0 1.268-.63 2.39-1.593 3.068a3.745 3.745 0 0 1-1.043 3.296 3.745 3.745 0 0 1-3.296 1.043A3.745 3.745 0 0 1 12 21c-1.268 0-2.39-.63-3.068-1.593a3.746 3.746 0 0 1-3.296-1.043 3.745 3.745 0 0 1-1.043-3.296A3.745 3.745 0 0 1 3 12c0-1.268.63-2.39 1.593-3.068a3.745 3.745 0 0 1 1.043-3.296 3.746 3.746 0 0 1 3.296-1.043A3.746 3.746 0 0 1 12 3c1.268 0 2.39.63 3.068 1.593a3.746 3.746 0 0 1 3.296 1.043 3.746 3.746 0 0 1 1.043 3.296A3.745 3.745 0 0 1 21 12Z" />
    </svg>
  ),
  dotacoes: (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
      <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 18.75a60.07 60.07 0 0 1 15.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 0 1 3 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 0 0-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 0 1-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 0 0 3 15h-.75M15 10.5a3 3 0 1 1-6 0 3 3 0 0 1 6 0Zm3 0h.008v.008H18V10.5Zm-12 0h.008v.008H6V10.5Z" />
    </svg>
  ),
  indicacoes: (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
    </svg>
  ),
  dfds: (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m6.75 12H9m1.5-12H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
    </svg>
  ),
  mapa: (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
      <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 6a7.5 7.5 0 1 0 7.5 7.5h-7.5V6Z" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 10.5H21A7.5 7.5 0 0 0 13.5 3v7.5Z" />
    </svg>
  ),
  etps: (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
      <path strokeLinecap="round" strokeLinejoin="round" d="M11.35 3.836c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 0 0 .75-.75 2.25 2.25 0 0 0-.1-.664m-5.8 0A2.251 2.251 0 0 1 13.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m8.9-4.414c.376.023.75.05 1.124.08 1.131.094 1.976 1.057 1.976 2.192V16.5A2.25 2.25 0 0 1 18 18.75h-2.25m-7.5-10.5H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V18.75m-7.5-10.5h6.375c.621 0 1.125.504 1.125 1.125v9.375m-8.25-3 1.5 1.5 3-3.75" />
    </svg>
  ),
  trs: (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 0 0 6 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 0 1 6 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 0 1 6-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0 0 18 18a8.967 8.967 0 0 0-6 2.292m0-14.25v14.25" />
    </svg>
  ),
  licitacao: (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 21v-8.25M15.75 21v-8.25M8.25 21v-8.25M3 9l9-6 9 6m-1.5 12V10.332A48.36 48.36 0 0 0 12 9.75c-2.551 0-5.056.2-7.5.582V21M3 21h18M12 6.75h.008v.008H12V6.75Z" />
    </svg>
  ),
  contratos: (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
      <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 17.25v3.375c0 .621-.504 1.125-1.125 1.125h-9.75a1.125 1.125 0 0 1-1.125-1.125V7.875c0-.621.504-1.125 1.125-1.125H6.75a9.06 9.06 0 0 1 1.5.124m7.5 10.376h3.375c.621 0 1.125-.504 1.125-1.125V11.25c0-4.46-3.243-8.161-7.5-8.876a9.06 9.06 0 0 0-1.5-.124H9.375c-.621 0-1.125.504-1.125 1.125v3.5m7.5 10.375H9.375a1.125 1.125 0 0 1-1.125-1.125v-9.25m12 6.625v-1.875a3.375 3.375 0 0 0-3.375-3.375h-1.5a1.125 1.125 0 0 1-1.125-1.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H9.75" />
    </svg>
  ),
  calendario: (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
      <path strokeLinecap="round" strokeLinejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 0 1 2.25-2.25h13.5A2.25 2.25 0 0 1 21 7.5v11.25m-18 0A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75m-18 0v-7.5A2.25 2.25 0 0 1 5.25 9h13.5A2.25 2.25 0 0 1 21 11.25v7.5m-9-6h.008v.008H12v-.008ZM12 15h.008v.008H12V15Zm0 2.25h.008v.008H12v-.008ZM9.75 15h.008v.008H9.75V15Zm0 2.25h.008v.008H9.75v-.008ZM7.5 15h.008v.008H7.5V15Zm0 2.25h.008v.008H7.5v-.008Zm6.75-4.5h.008v.008h-.008v-.008Zm0 2.25h.008v.008h-.008V15Zm0 2.25h.008v.008h-.008v-.008Zm2.25-4.5h.008v.008H16.5v-.008Zm0 2.25h.008v.008H16.5V15Z" />
    </svg>
  ),
  fornecedores: (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
      <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21" />
    </svg>
  ),
  fesp: (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 21a9 9 0 1 0-9-9c0 1.657.5 3.194 1.357 4.474L3 21l4.526-1.357A8.96 8.96 0 0 0 12 21Z" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 8.25v7.5m-2.25-6h3a1.5 1.5 0 0 1 0 3h-1.5a1.5 1.5 0 0 0 0 3h3" />
    </svg>
  ),
  config: (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
      <path strokeLinecap="round" strokeLinejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 0 1 1.37.49l1.296 2.247a1.125 1.125 0 0 1-.26 1.431l-1.003.827c-.293.241-.438.613-.43.992a7.723 7.723 0 0 1 0 .255c-.008.378.137.75.43.991l1.004.827c.424.35.534.955.26 1.43l-1.298 2.247a1.125 1.125 0 0 1-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.47 6.47 0 0 1-.22.128c-.331.183-.581.495-.644.869l-.213 1.281c-.09.543-.56.94-1.11.94h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 0 1-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 0 1-1.369-.49l-1.297-2.247a1.125 1.125 0 0 1 .26-1.431l1.004-.827c.292-.24.437-.613.43-.991a6.932 6.932 0 0 1 0-.255c.007-.38-.138-.751-.43-.992l-1.004-.827a1.125 1.125 0 0 1-.26-1.43l1.297-2.247a1.125 1.125 0 0 1 1.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.086.22-.128.332-.183.582-.495.644-.869l.214-1.28Z" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
    </svg>
  ),
}

// ── Definição dos módulos ──────────────────────────────────────────────────────
// requiredPapeis: ['*'] = todos | lista específica = apenas esses papeis
// requiredFlags: flags do authStore que devem ser true (ausente = sem restrição)
// requiredUnidades: tipoUnidade que também autoriza acesso além dos papeis
export const MODULE_CARDS_DEF = [
  {
    id: 'painel',
    label: 'Painel de Demandas',
    descricao: 'Acompanhe o ciclo das demandas',
    cor: 'slate',
    to: '/painel',
    requiredPapeis: ['*'],
    requiredFlags: [],
    requiredUnidades: [],
    icon: icons.painel,
  },
  {
    id: 'plano_compras',
    label: 'Plano de Compras',
    descricao: 'Planejamento anual de aquisições',
    cor: 'slate',
    to: '/plano-compras',
    requiredPapeis: ['analista', 'gestor_planejamento', 'ordenador', 'admin'],
    requiredFlags: [],
    requiredUnidades: ['licitante', 'planejamento'],
    icon: icons.plano_compras,
  },
  {
    id: 'necessidades',
    label: 'Necessidades',
    descricao: 'Registre e gerencie necessidades',
    cor: 'emerald',
    to: '/planejamento/necessidades',
    requiredPapeis: ['analista', 'gestor_planejamento', 'solicitante', 'admin'],
    requiredFlags: ['modulo_planejamento_ativo'],
    requiredUnidades: ['planejamento'],
    icon: icons.necessidades,
  },
  {
    id: 'aceite',
    label: 'Aceite de Necessidades',
    descricao: 'Revise demandas de órgãos filhos',
    cor: 'amber',
    to: '/planejamento/aceite',
    requiredPapeis: ['gestor_planejamento', 'admin'],
    requiredFlags: ['modulo_planejamento_ativo'],
    requiredUnidades: ['planejamento'],
    icon: icons.aceite,
  },
  {
    id: 'dotacoes',
    label: 'Dotações Orçamentárias',
    descricao: 'Gerencie dotações e execução',
    cor: 'yellow',
    to: '/orcamento/dotacoes',
    requiredPapeis: ['analista', 'gestor_planejamento', 'ordenador', 'admin'],
    requiredFlags: ['modulo_orcamento_ativo'],
    requiredUnidades: ['planejamento'],
    icon: icons.dotacoes,
  },
  {
    id: 'indicacoes',
    label: 'Indicações / DOD',
    descricao: 'Indicações de dotação orçamentária',
    cor: 'yellow',
    to: '/orcamento/indicacoes',
    requiredPapeis: ['analista', 'gestor_planejamento', 'ordenador', 'admin'],
    requiredFlags: ['modulo_orcamento_ativo'],
    requiredUnidades: ['planejamento'],
    icon: icons.indicacoes,
  },
  {
    id: 'fesp_planos',
    label: 'Plano de Aplicação FESP',
    descricao: 'FESP, emendas e financiamentos',
    cor: 'amber',
    to: '/fesp/planos',
    requiredPapeis: ['analista', 'gestor_planejamento', 'ordenador', 'admin'],
    requiredFlags: ['modulo_fesp_ativo'],
    requiredUnidades: ['planejamento'],
    icon: icons.fesp,
  },
  {
    id: 'dfds',
    label: 'DFDs',
    descricao: 'Documentos de Formalização de Demanda',
    cor: 'blue',
    to: '/demanda/dfd',
    requiredPapeis: ['analista', 'gestor_contrato', 'fiscal_contrato', 'responsavel_tecnico', 'solicitante', 'admin'],
    requiredFlags: [],
    requiredUnidades: ['demandante'],
    icon: icons.dfds,
  },
  {
    id: 'mapa',
    label: 'Mapa Comparativo',
    descricao: 'Pesquisa de preços e cotações',
    cor: 'violet',
    to: '/pesquisa/mapa',
    requiredPapeis: ['analista', 'responsavel_tecnico', 'solicitante', 'admin'],
    requiredFlags: ['modulo_mapa_ativo'],
    requiredUnidades: ['licitante', 'demandante'],
    icon: icons.mapa,
  },
  {
    id: 'etps',
    label: 'ETPs',
    descricao: 'Estudos Técnicos Preliminares',
    cor: 'indigo',
    to: '/etp/etps',
    requiredPapeis: ['analista', 'gestor_contrato', 'responsavel_tecnico', 'solicitante', 'admin'],
    requiredFlags: ['modulo_etp_ativo'],
    requiredUnidades: ['licitante'],
    icon: icons.etps,
  },
  {
    id: 'trs',
    label: 'Minutas TR',
    descricao: 'Termos de Referência',
    cor: 'indigo',
    to: '/analise-tecnica/trs',
    requiredPapeis: ['analista', 'gestor_contrato', 'responsavel_tecnico', 'solicitante', 'admin'],
    requiredFlags: [],
    requiredUnidades: ['licitante'],
    icon: icons.trs,
  },
  {
    id: 'licitacao',
    label: 'Procedimentos',
    descricao: 'Gerencie processos licitatórios',
    cor: 'orange',
    to: '/licitacao',
    requiredPapeis: ['analista', 'gestor_contrato', 'ordenador', 'admin'],
    requiredFlags: [],
    requiredUnidades: ['licitante', 'contratante'],
    icon: icons.licitacao,
  },
  {
    id: 'contratos',
    label: 'Contratos',
    descricao: 'Gestão de contratos vigentes',
    cor: 'teal',
    to: '/contratos',
    requiredPapeis: ['analista', 'gestor_contrato', 'fiscal_contrato', 'ordenador', 'admin'],
    requiredFlags: [],
    requiredUnidades: ['licitante', 'contratante'],
    icon: icons.contratos,
  },
  {
    id: 'fornecedores',
    label: 'Fornecedores',
    descricao: 'Cadastro único, CNPJ/CPF e histórico',
    cor: 'sky',
    to: '/fornecedores',
    requiredPapeis: ['analista', 'gestor_contrato', 'ordenador', 'admin'],
    requiredFlags: [],
    requiredUnidades: ['licitante', 'contratante'],
    icon: icons.fornecedores,
  },
  {
    id: 'calendario',
    label: 'Calendário',
    descricao: 'Linha do tempo das contratações',
    cor: 'teal',
    to: '/calendario',
    requiredPapeis: ['analista', 'gestor_planejamento', 'gestor_contrato', 'fiscal_contrato', 'ordenador', 'admin'],
    requiredFlags: [],
    requiredUnidades: ['licitante', 'contratante', 'planejamento'],
    icon: icons.calendario,
  },
  {
    id: 'config',
    label: 'Configurações',
    descricao: 'Parâmetros e administração',
    cor: 'gray',
    to: '/config/parametros',
    requiredPapeis: ['admin', 'gestor_planejamento'],
    requiredFlags: [],
    requiredUnidades: ['licitante', 'planejamento'],
    icon: icons.config,
  },
]

// ── Função de filtragem por perfil ────────────────────────────────────────────
export function buildModuleCards(papel, tipoUnidade, flags = {}) {
  return MODULE_CARDS_DEF.filter(card => {
    // Verificar permissão de papel/unidade
    const temAcessoPapel =
      card.requiredPapeis.includes('*') ||
      card.requiredPapeis.includes(papel) ||
      card.requiredUnidades.includes(tipoUnidade)

    if (!temAcessoPapel) return false

    // Verificar flags de módulos ativos
    for (const flag of card.requiredFlags) {
      if (flags[flag] === false) return false
    }

    return true
  })
}
