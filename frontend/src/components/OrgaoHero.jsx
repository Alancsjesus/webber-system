import { getOrgaoLogo } from '../config/orgaoLogos'

const TIPO_UNIDADE_BADGE = {
  demandante:   { label: 'Demandante',   cls: 'bg-purple-800/80 text-purple-200' },
  licitante:    { label: 'Licitante',    cls: 'bg-blue-800/80 text-blue-200'     },
  contratante:  { label: 'Contratante',  cls: 'bg-green-800/80 text-green-200'   },
  planejamento: { label: 'Planejamento', cls: 'bg-orange-800/80 text-orange-200' },
}

function iniciais(nome) {
  if (!nome) return 'W'
  const partes = nome.trim().split(/\s+/)
  return partes
    .filter(p => p.length > 2)
    .slice(0, 2)
    .map(p => p[0].toUpperCase())
    .join('') || nome[0].toUpperCase()
}

export default function OrgaoHero({ orgaoSigla, orgaoNome, unidadeNome, tipoUnidade, papel }) {
  const logoSrc = getOrgaoLogo(orgaoSigla, 'brasao')
  const badge   = TIPO_UNIDADE_BADGE[tipoUnidade]

  return (
    <div className="flex flex-col items-center gap-3 pb-5 pt-2 text-center">
      {/* Brasão ou fallback com iniciais */}
      {logoSrc ? (
        <img
          src={logoSrc}
          alt={`Brasão ${orgaoSigla}`}
          className="h-20 w-20 object-contain drop-shadow-xl"
        />
      ) : (
        <div className="w-20 h-20 rounded-2xl bg-gray-800 border-2 border-gray-700 flex items-center justify-center shrink-0">
          <span className="text-3xl font-black text-gray-200 select-none">
            {iniciais(orgaoNome)}
          </span>
        </div>
      )}

      {/* Nome do órgão */}
      <div>
        <p className="text-xl font-bold text-white leading-tight">
          {orgaoSigla && <span className="text-gray-300 font-black">{orgaoSigla}</span>}
          {orgaoSigla && orgaoNome && <span className="text-gray-500 mx-2">·</span>}
          {orgaoNome && <span>{orgaoNome}</span>}
          {!orgaoSigla && !orgaoNome && <span className="text-gray-400">Weber-e</span>}
        </p>
      </div>

      {/* Badges tipo unidade + papel */}
      <div className="flex items-center gap-2 flex-wrap justify-center">
        {badge && (
          <span className={`px-2.5 py-0.5 rounded-md text-[11px] font-semibold ${badge.cls}`}>
            {badge.label}
          </span>
        )}
        {papel && (
          <span className="px-2.5 py-0.5 rounded-md text-[11px] font-medium bg-gray-800 text-gray-300 capitalize">
            {papel.replace(/_/g, ' ')}
          </span>
        )}
      </div>

      {/* Nome da unidade */}
      {unidadeNome && (
        <p className="text-sm text-gray-500 -mt-1">{unidadeNome}</p>
      )}
    </div>
  )
}
