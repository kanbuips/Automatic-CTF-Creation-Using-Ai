import { useState } from "react";
import { useNavigate } from "react-router-dom";
import Button from "../../components/common/Button";
import PageContainer from "../../components/layout/PageContainer";
import { useAuthStore } from "../../store";

export default function Login() {
  const { apiKey, setApiKey } = useAuthStore();
  const [value, setValue] = useState(apiKey);
  const navigate = useNavigate();
  return (
    <PageContainer title="API key">
      <form className="form" onSubmit={(e) => { e.preventDefault(); setApiKey(value.trim()); navigate("/"); }}>
        <p className="muted">Leave empty if the server does not require a key.</p>
        <input type="password" value={value} onChange={(e) => setValue(e.target.value)} placeholder="X-API-Key" />
        <Button type="submit">Save</Button>
      </form>
    </PageContainer>
  );
}
