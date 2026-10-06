import { BrowserRouter, Route, Routes } from "react-router-dom";
import Approval from "../pages/Approval/Approval";
import Dashboard from "../pages/Dashboard/Dashboard";
import Login from "../pages/Login/Login";
import ReportView from "../pages/ReportView/ReportView";
import Upload from "../pages/Upload/Upload";
import ValidationResult from "../pages/ValidationResult/ValidationResult";

export default function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/login" element={<Login />} />
        <Route path="/upload" element={<Upload />} />
        <Route path="/jobs/:jobId" element={<ValidationResult />} />
        <Route path="/reports/:id" element={<ReportView />} />
        <Route path="/approval/:id" element={<Approval />} />
      </Routes>
    </BrowserRouter>
  );
}
