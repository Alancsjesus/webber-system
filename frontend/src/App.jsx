import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import ProtectedRoute from './components/ProtectedRoute'
import Layout from './components/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import DFDList from './pages/DFDList'
import DFDCreate from './pages/DFDCreate'
import DFDDetail from './pages/DFDDetail'
import NecessidadeList from './pages/NecessidadeList'
import NecessidadeCreate from './pages/NecessidadeCreate'
import NecessidadeDetail from './pages/NecessidadeDetail'
import AceiteNecessidades from './pages/AceiteNecessidades'
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
import Ajuda from './pages/Ajuda'
import Painel from './pages/Painel'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />

        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Dashboard />} />

          {/* Painel e Ajuda */}
          <Route path="painel" element={<Painel />} />
          <Route path="ajuda"  element={<Ajuda />} />

          {/* Planejamento */}
          <Route path="planejamento/necessidades"       element={<NecessidadeList />} />
          <Route path="planejamento/necessidades/nova"  element={<NecessidadeCreate />} />
          <Route path="planejamento/necessidades/:id"   element={<NecessidadeDetail />} />
          <Route path="planejamento/aceite"             element={<AceiteNecessidades />} />

          {/* Orçamento */}
          <Route path="orcamento/dotacoes"          element={<OrcamentoList />} />
          <Route path="orcamento/dotacoes/nova"     element={<OrcamentoCreate />} />
          <Route path="orcamento/dotacoes/:id"      element={<OrcamentoDetail />} />
          <Route path="orcamento/indicacoes"        element={<IndicacaoList />} />
          <Route path="orcamento/indicacoes/nova"   element={<IndicacaoCreate />} />
          <Route path="orcamento/indicacoes/:id"    element={<IndicacaoDetail />} />

          {/* Demanda */}
          <Route path="demanda/dfd"       element={<DFDList />} />
          <Route path="demanda/dfd/novo"  element={<DFDCreate />} />
          <Route path="demanda/dfd/:id"   element={<DFDDetail />} />

          {/* ETP */}
          <Route path="etp/etps"      element={<ETPList />} />
          <Route path="etp/etps/novo" element={<ETPCreate />} />
          <Route path="etp/etps/:id"  element={<ETPDetail />} />

          {/* TR */}
          <Route path="analise-tecnica/trs"      element={<TRList />} />
          <Route path="analise-tecnica/trs/novo" element={<TRCreate />} />
          <Route path="analise-tecnica/trs/:id"  element={<TRDetail />} />

          {/* Configurações */}
          <Route path="config/orgaos"    element={<OrgaoAdmin />} />
          <Route path="config/unidades"  element={<UnidadeAdmin />} />
          <Route path="config/usuarios"  element={<UsuarioAdmin />} />
          <Route path="config/acoes"     element={<AcaoAdmin />} />
          <Route path="config/elementos" element={<ElementoAdmin />} />
          <Route path="config/naturezas" element={<NaturezaAdmin />} />
          <Route path="config/fontes"    element={<FonteAdmin />} />

          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
