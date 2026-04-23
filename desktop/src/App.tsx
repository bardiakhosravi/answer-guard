import { Routes, Route, Navigate } from "react-router-dom";
import AppShell from "./components/AppShell";
import ConnectScreen from "./screens/ConnectScreen";
import DetailsScreen from "./screens/connector/DetailsScreen";
import SchemaScreen from "./screens/connector/SchemaScreen";
import ReviewScreen from "./screens/connector/ReviewScreen";
import ImportScreen from "./screens/ImportScreen";
import DataScreen from "./screens/DataScreen";
import ResponseFeedbackScreen from "./screens/ResponseFeedbackScreen";

export default function App() {
  return (
    <Routes>
      <Route path="/connect" element={<ConnectScreen />} />
      <Route element={<AppShell />}>
        <Route path="/connector" element={<Navigate to="/connector/details" replace />} />
        <Route path="/connector/details" element={<DetailsScreen />} />
        <Route path="/connector/schema" element={<SchemaScreen />} />
        <Route path="/connector/review" element={<ReviewScreen />} />
        <Route path="/import" element={<ImportScreen />} />
        <Route path="/data" element={<DataScreen />} />
        <Route path="/response-feedback" element={<ResponseFeedbackScreen />} />
        <Route path="*" element={<Navigate to="/connector/details" replace />} />
      </Route>
    </Routes>
  );
}
