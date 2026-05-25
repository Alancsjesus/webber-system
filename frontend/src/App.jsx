import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import ProtectedRoute from './components/ProtectedRoute'
import RequireRole from './components/RequireRole'
import Layout from './components/Layout'
import Login from './pages/Login'
import SemAcesso from './pages/SemAcesso'
import Dashboard from './pages/Dashboard'
import DFDList from './pages/DFDList'
import DFDCreate from './pages/DFDCreate'
import DFDDetail from './pages/DFDDetail'
import NecessidadeList from './pages/NecessidadeList'
import NecessidadeCreate from './pages/NecessidadeCreate'
import NecessidadeDetail from './pages/NecessidadeDetail'
import AceiteNecessidades from './pages/AceiteNecessidades'
import MapaList from './pages/MapaList'
import MapaCreate from './pages/MapaCreate'
import MapaDetail from './pages/MapaDetail'
import OrcamentoList from './pages/OrcamentoList'
import OrcamentoCreate from './pages/OrcamentoCreate'
import OrcamentoDetail from './pages/OrcamentoDetail'
import IndicacaoList from './pages/IndicacaoList'
import IndicacaoCreate from './pages/IndicacaoCreate'
import IndicacaoDetail from './pages/IndicacaoDetail'
import ETPList from './pages/ETPList'
import ETPCreate from './pages/ETPCreate'
import ETPDetail from './pages/ETPDetail'
import TRList from './pages/TRList'
import TRCreate from './pages/TRCreate'
import TRDetail from './pages/TRDetail'
import OrgaoAdmin from './pages/config/OrgaoAdmin'
import UnidadeAdmin from './pages/config/UnidadeAdmin'
import UsuarioAdmin from './pages/config/UsuarioAdmin'
import AcaoAdmin from './pages/config/AcaoAdmin'
import ElementoAdmin from './pages/config/ElementoAdmin'
import NaturezaAdmin from './pages/config/NaturezaAdmin'
import FonteAdmin from './pages/config/FonteAdmin'
import ParametroAdmin from './pages/config/ParametroAdmin'
import PerfilAdmin from './pages/config/PerfilAdmin'
import AreaAdmin from './pages/config/AreaAdmin'
import ArtefatoAdmin from './pages/config/ArtefatoAdmin'
import CatalogoAdmin from './pages/config/CatalogoAdmin'
import CategoriaAdmin from './pages/config/CategoriaAdmin'
import ImportarCatalogoAdmin from './pages/config/ImportarCatalogoAdmin'
import Ajuda from './pages/Ajuda'
import Painel from './pages/Painel'
import PlanoCompras from './pages/PlanoCompras'
import ContratoList from './pages/ContratoList'
import ContratoCreate from './pages/ContratoCreate'
import ContratoDetail from './pages/ContratoDetail'
import ProcedimentoList from './pages/ProcedimentoList'
import ProcedimentoCreate from './pages/ProcedimentoCreate'
import ProcedimentoDetail from './pages/ProcedimentoDetail'
import PrepararAquisicao from './pages/PrepararAquisicao'
import Calendario from './pages/Calendario'
import PCADetail from './pages/PCADetail'
import PlanoList from './pages/PlanoList'
import PNCPList from './pages/PNCPList'
import AuditoriaList from './pages/AuditoriaList'
import RastreabilidadeList from './pages/RastreabilidadeList'
import RastreabilidadeDetail from './pages/RastreabilidadeDetail'

// Wrapper que combina autenticação + autorização por papel
function Guard({ children }) {
  return (
    <ProtectedRoute>
      <RequireRole>{children}</RequireRole>
    </ProtectedRoute>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login"      element={<Login />} />
        <Route path="/sem-acesso" element={<SemAcesso />} />

        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          {/* Dashboard — todos os autenticados */}
          <Route index element={<Dashboard />} />

          {/* Painel e Ajuda — todos */}
          <Route path="painel"        element={<Guard><Painel /></Guard>} />
          <Route path="ajuda"         element={<Guard><Ajuda /></Guard>} />
          <Route path="plano-compras"          element={<Guard><PlanoCompras /></Guard>} />
          <Route path="planejamento/planos"    element={<Guard><PlanoList /></Guard>} />
          <Route path="planejamento/pca/:id"   element={<Guard><PCADetail /></Guard>} />
          <Route path="calendario"             element={<Guard><Calendario /></Guard>} />
          <Route path="aquisicao/preparar" element={<Guard><PrepararAquisicao /></Guard>} />

          {/* Planejamento */}
          <Route path="planejamento/necessidades"      element={<Guard><NecessidadeList /></Guard>} />
          <Route path="planejamento/necessidades/nova" element={<Guard><NecessidadeCreate /></Guard>} />
          <Route path="planejamento/necessidades/:id"  element={<Guard><NecessidadeDetail /></Guard>} />
          <Route path="planejamento/aceite"            element={<Guard><AceiteNecessidades /></Guard>} />

          {/* Pesquisa de Preços */}
          <Route path="pesquisa/mapa"      element={<Guard><MapaList /></Guard>} />
          <Route path="pesquisa/mapa/novo" element={<Guard><MapaCreate /></Guard>} />
          <Route path="pesquisa/mapa/:id"  element={<Guard><MapaDetail /></Guard>} />
          <Route path="pesquisa/pncp"      element={<Guard><PNCPList /></Guard>} />

          {/* Orçamento */}
          <Route path="orcamento/dotacoes"         element={<Guard><OrcamentoList /></Guard>} />
          <Route path="orcamento/dotacoes/nova"    element={<Guard><OrcamentoCreate /></Guard>} />
          <Route path="orcamento/dotacoes/:id"     element={<Guard><OrcamentoDetail /></Guard>} />
          <Route path="orcamento/indicacoes"       element={<Guard><IndicacaoList /></Guard>} />
          <Route path="orcamento/indicacoes/nova"  element={<Guard><IndicacaoCreate /></Guard>} />
          <Route path="orcamento/indicacoes/:id"   element={<Guard><IndicacaoDetail /></Guard>} />

          {/* Demanda */}
          <Route path="demanda/dfd"      element={<Guard><DFDList /></Guard>} />
          <Route path="demanda/dfd/novo" element={<Guard><DFDCreate /></Guard>} />
          <Route path="demanda/dfd/:id"  element={<Guard><DFDDetail /></Guard>} />

          {/* ETP */}
          <Route path="etp/etps"      element={<Guard><ETPList /></Guard>} />
          <Route path="etp/etps/novo" element={<Guard><ETPCreate /></Guard>} />
          <Route path="etp/etps/:id"  element={<Guard><ETPDetail /></Guard>} />

          {/* TR */}
          <Route path="analise-tecnica/trs"      element={<Guard><TRList /></Guard>} />
          <Route path="analise-tecnica/trs/novo" element={<Guard><TRCreate /></Guard>} />
          <Route path="analise-tecnica/trs/:id"  element={<Guard><TRDetail /></Guard>} />

          {/* Licitação */}
          <Route path="licitacao"      element={<Guard><ProcedimentoList /></Guard>} />
          <Route path="licitacao/novo" element={<Guard><ProcedimentoCreate /></Guard>} />
          <Route path="licitacao/:id"  element={<Guard><ProcedimentoDetail /></Guard>} />

          {/* Contratos */}
          <Route path="contratos"      element={<Guard><ContratoList /></Guard>} />
          <Route path="contratos/novo" element={<Guard><ContratoCreate /></Guard>} />
          <Route path="contratos/:id"  element={<Guard><ContratoDetail /></Guard>} />

          {/* Configurações — somente admin */}
          <Route path="config/orgaos"    element={<Guard><OrgaoAdmin /></Guard>} />
          <Route path="config/unidades"  element={<Guard><UnidadeAdmin /></Guard>} />
          <Route path="config/usuarios"  element={<Guard><UsuarioAdmin /></Guard>} />
          <Route path="config/perfis"    element={<Guard><PerfilAdmin /></Guard>} />
          <Route path="config/parametros"element={<Guard><ParametroAdmin /></Guard>} />
          <Route path="config/areas"     element={<Guard><AreaAdmin /></Guard>} />
          <Route path="config/acoes"     element={<Guard><AcaoAdmin /></Guard>} />
          <Route path="config/elementos" element={<Guard><ElementoAdmin /></Guard>} />
          <Route path="config/naturezas" element={<Guard><NaturezaAdmin /></Guard>} />
          <Route path="config/fontes"    element={<Guard><FonteAdmin /></Guard>} />
          <Route path="config/artefatos" element={<Guard><ArtefatoAdmin /></Guard>} />
          <Route path="config/catalogo"          element={<Guard><CatalogoAdmin /></Guard>} />
          <Route path="config/catalogo/importar" element={<Guard><ImportarCatalogoAdmin /></Guard>} />
          <Route path="config/categorias"        element={<Guard><CategoriaAdmin /></Guard>} />
          <Route path="auditoria"                  element={<Guard><AuditoriaList /></Guard>} />
          <Route path="rastreabilidade"            element={<Guard><RastreabilidadeList /></Guard>} />
          <Route path="rastreabilidade/:id"        element={<Guard><RastreabilidadeDetail /></Guard>} />

          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
