import { NavLink } from "react-router-dom";

export default function Sidebar() {
  return (
    <nav className="sidebar">
      <strong>CTF QC</strong>
      <NavLink to="/" end>Dashboard</NavLink>
      <NavLink to="/upload">New validation</NavLink>
      <NavLink to="/login">API key</NavLink>
    </nav>
  );
}
