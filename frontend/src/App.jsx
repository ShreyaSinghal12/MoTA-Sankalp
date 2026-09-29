import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout.jsx";
import { getToken } from "./api.js";
import Login from "./pages/Login.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Applications from "./pages/Applications.jsx";
import ApplicationDetail from "./pages/ApplicationDetail.jsx";
import Home from "./pages/Home.jsx";
import DocumentAnalyzer from "./pages/DocumentAnalyzer.jsx";

function Protected({ children }) {
  return getToken() ? <Layout>{children}</Layout> : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/home" replace />} />
      <Route path="/home" element={<Home />} />
      <Route path="/login" element={<Login />} />
      <Route path="/dashboard" element={<Protected><Dashboard /></Protected>} />
      <Route path="/applications" element={<Protected><Applications /></Protected>} />
      <Route path="/applications/:id" element={<Protected><ApplicationDetail /></Protected>} />
<Route
  path="/documents"
  element={
    <Protected>
      <DocumentAnalyzer />
    </Protected>
  }
/>
      <Route path="*" element={<Navigate to={getToken() ? "/dashboard" : "/home"} replace />} />
    </Routes>
  );
}
