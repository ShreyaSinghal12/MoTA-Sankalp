import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout.jsx";
import { getToken } from "./api.js";
import Login from "./pages/Login.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Applications from "./pages/Applications.jsx";
import ApplicationDetail from "./pages/ApplicationDetail.jsx";

function Protected({ children }) {
  return getToken() ? <Layout>{children}</Layout> : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/dashboard" element={<Protected><Dashboard /></Protected>} />
      <Route path="/applications" element={<Protected><Applications /></Protected>} />
      <Route path="/applications/:id" element={<Protected><ApplicationDetail /></Protected>} />
      <Route path="*" element={<Navigate to={getToken() ? "/dashboard" : "/login"} replace />} />
    </Routes>
  );
}
