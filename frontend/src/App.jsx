import { useEffect, useState } from "react";

const API_BASE = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");

const apiUrl = (path) => `${API_BASE}${path}`;

const graphQlRequest = async (query, variables = {}) => {
  const tryPaths = ["/graphql/", "/graphql"];
  let lastError = "Request failed.";

  for (const path of tryPaths) {
    try {
      const response = await fetch(apiUrl(path), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify({ query, variables }),
      });

      const raw = await response.text();
      let payload = null;
      try {
        payload = raw ? JSON.parse(raw) : null;
      } catch {
        payload = null;
      }

      if (!response.ok) {
        lastError = payload?.errors?.map((item) => item.message).join(", ") || `Request failed (${response.status}).`;
        continue;
      }

      if (!payload) {
        lastError = `Server returned an empty response (${response.status}).`;
        continue;
      }

      if (payload.errors?.length) {
        throw new Error(payload.errors.map((item) => item.message).join(", "));
      }

      return payload.data;
    } catch (error) {
      lastError = error.message;
    }
  }

  throw new Error(lastError);
};

const fileToBase64 = async (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result;
      resolve(result.split(",")[1]);
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
};

const downloadFile = (base64Content, fileName) => {
  const binaryString = atob(base64Content);
  const bytes = new Uint8Array(binaryString.length);
  for (let index = 0; index < binaryString.length; index += 1) {
    bytes[index] = binaryString.charCodeAt(index);
  }
  const blob = new Blob([bytes], {
    type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = fileName;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
};

const statusLabels = {
  healthy: "System ready",
  loading: "Checking system",
  error: "Needs attention",
};

function App() {
  const [rulesInfo, setRulesInfo] = useState({ exists: false, path: "" });
  const [status, setStatus] = useState("loading");
  const [message, setMessage] = useState("Checking the current setup...");
  const [busy, setBusy] = useState({ rules: false, employees: false, refresh: false, downloadRules: false, downloadTemplate: false });
  const [lastResult, setLastResult] = useState(null);

  const refreshSummary = async () => {
    setBusy((current) => ({ ...current, refresh: true }));
    try {
      const payload = await graphQlRequest(`
        query DashboardStatus {
          health
          rulesWorkbook {
            path
            exists
          }
        }
      `);
      setRulesInfo(payload.rulesWorkbook);
      setStatus(payload.health === "ok" ? "healthy" : "error");
      setMessage(payload.rulesWorkbook.exists ? "Rules workbook is ready for HR use." : "Rules workbook not found yet.");
    } catch (error) {
      setStatus("error");
      setMessage(error.message);
    } finally {
      setBusy((current) => ({ ...current, refresh: false }));
    }
  };

  useEffect(() => {
    refreshSummary();
  }, []);

  const handleDownloadRules = async () => {
    setBusy((current) => ({ ...current, downloadRules: true }));
    try {
      const payload = await graphQlRequest(`
        query DownloadRules {
          downloadRules {
            fileName
            fileContent
          }
        }
      `);
      downloadFile(payload.downloadRules.fileContent, payload.downloadRules.fileName);
      setStatus("healthy");
      setMessage("Salary rules workbook downloaded.");
    } catch (error) {
      setStatus("error");
      setMessage(error.message);
    } finally {
      setBusy((current) => ({ ...current, downloadRules: false }));
    }
  };

  const handleDownloadTemplate = async () => {
    setBusy((current) => ({ ...current, downloadTemplate: true }));
    try {
      const payload = await graphQlRequest(`
        query DownloadTemplate {
          downloadEmployeeTemplate {
            fileName
            fileContent
          }
        }
      `);
      downloadFile(payload.downloadEmployeeTemplate.fileContent, payload.downloadEmployeeTemplate.fileName);
      setStatus("healthy");
      setMessage("Employee template downloaded.");
    } catch (error) {
      setStatus("error");
      setMessage(error.message);
    } finally {
      setBusy((current) => ({ ...current, downloadTemplate: false }));
    }
  };

  const handleRulesUpload = async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const file = form.elements.rules.files[0];
    if (!file) {
      setStatus("error");
      setMessage("Choose the updated salary rules workbook first.");
      return;
    }

    setBusy((current) => ({ ...current, rules: true }));
    try {
      const base64Content = await fileToBase64(file);
      await graphQlRequest(
        `mutation UploadRules($fileContent: String!, $fileName: String!) {
          uploadRules(fileContent: $fileContent, fileName: $fileName)
        }`,
        {
          fileContent: base64Content,
          fileName: file.name,
        }
      );
      setStatus("healthy");
      setMessage("Updated salary rules uploaded successfully.");
      await refreshSummary();
    } catch (error) {
      setStatus("error");
      setMessage(error.message);
    } finally {
      setBusy((current) => ({ ...current, rules: false }));
      form.reset();
    }
  };

  const handleEmployeeUpload = async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const file = form.elements.employees.files[0];
    if (!file) {
      setStatus("error");
      setMessage("Choose the employee spreadsheet first.");
      return;
    }

    setBusy((current) => ({ ...current, employees: true }));
    try {
      const base64Content = await fileToBase64(file);
      const payload = await graphQlRequest(
        `mutation ProcessEmployees($fileContent: String!, $fileName: String!) {
          processEmployees(fileContent: $fileContent, fileName: $fileName) {
            processedRows
            successRows
            errorRows
            fileName
            fileContent
          }
        }`,
        {
          fileContent: base64Content,
          fileName: file.name,
        }
      );
      const summary = payload.processEmployees;
      downloadFile(summary.fileContent, summary.fileName);

      setLastResult({
        processedRows: summary.processedRows,
        successRows: summary.successRows,
        errorRows: summary.errorRows,
        fileName: summary.fileName,
      });
      setStatus("healthy");
      setMessage("Processed file is ready and has been downloaded.");
    } catch (error) {
      setStatus("error");
      setMessage(error.message);
    } finally {
      setBusy((current) => ({ ...current, employees: false }));
      form.reset();
    }
  };

  return (
    <div className="shell">
      <main className="page">
        <section className="hero">
          <div className="hero-copy-block">
            <p className="eyebrow">HR Salary Desk</p>
            <h1>Manage salary sheets without touching code.</h1>
            <p className="hero-copy">
              Download the current salary rules, update them in Excel, upload employee data, and get the finished payroll sheet back.
            </p>
            <div className="hero-actions">
              <button className="primary-button" onClick={handleDownloadTemplate} disabled={busy.downloadTemplate}>
                {busy.downloadTemplate ? "Downloading..." : "Download employee template"}
              </button>
              <button className="secondary-button" onClick={handleDownloadRules} disabled={busy.downloadRules}>
                {busy.downloadRules ? "Downloading..." : "Download salary rules"}
              </button>
            </div>
          </div>
          <div className={`status-panel status-${status}`}>
            <div className="status-topline">
              <span className="status-dot" />
              <p className="status-label">{statusLabels[status]}</p>
            </div>
            <p className="status-message">{message}</p>
            <button className="secondary-button" onClick={refreshSummary} disabled={busy.refresh}>
              {busy.refresh ? "Refreshing..." : "Refresh status"}
            </button>
          </div>
        </section>

        <section className="grid">
          <article className="card action-card">
            <span className="step">01</span>
            <h2>Prepare files</h2>
            <p>Start with the latest rules and template so every workbook follows the expected format.</p>
            <div className="mini-note">
              <strong>Current rules file:</strong>
              <span>{rulesInfo.exists ? rulesInfo.path : "No rules workbook available yet."}</span>
            </div>
          </article>

          <article className="card action-card">
            <span className="step">02</span>
            <h2>Update rules</h2>
            <p>Upload the edited salary rules workbook after changing percentages, thresholds, caps, or formulas.</p>
            <form onSubmit={handleRulesUpload} className="stack">
              <input name="rules" type="file" accept=".xlsx" />
              <button className="primary-button" type="submit" disabled={busy.rules}>
                {busy.rules ? "Uploading..." : "Upload updated rules"}
              </button>
            </form>
          </article>

          <article className="card action-card">
            <span className="step">03</span>
            <h2>Process payroll</h2>
            <p>Upload the employee workbook and the finished salary sheet will download automatically.</p>
            <form onSubmit={handleEmployeeUpload} className="stack">
              <input name="employees" type="file" accept=".xlsx" />
              <button className="primary-button warm" type="submit" disabled={busy.employees}>
                {busy.employees ? "Processing..." : "Process employee workbook"}
              </button>
            </form>
          </article>
        </section>

        <section className="card summary-card">
          <div className="summary-head">
            <div>
              <p className="eyebrow">Latest run</p>
              <h2>Processing summary</h2>
            </div>
          </div>

          {lastResult ? (
            <div className="summary-grid">
              <div className="metric">
                <span>Processed rows</span>
                <strong>{lastResult.processedRows}</strong>
              </div>
              <div className="metric">
                <span>Successful rows</span>
                <strong>{lastResult.successRows}</strong>
              </div>
              <div className="metric">
                <span>Rows with issues</span>
                <strong>{lastResult.errorRows}</strong>
              </div>
              <div className="metric wide">
                <span>Downloaded file</span>
                <strong>{lastResult.fileName}</strong>
              </div>
            </div>
          ) : (
            <div className="empty-state">
              Upload an employee sheet to see the latest processing summary here.
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;
