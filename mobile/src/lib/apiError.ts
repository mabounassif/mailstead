export class ApiError extends Error {
  status: number;
  code: string;
  detail: string;
  fields: Record<string, string[]>;

  constructor(
    status: number,
    code: string,
    detail = "",
    fields: Record<string, string[]> = {},
  ) {
    super(detail || code);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.detail = detail;
    this.fields = fields;
  }
}

export function messageFromApiError(error: unknown): string {
  if (error instanceof ApiError) {
    const field = Object.values(error.fields)[0]?.[0];
    return field || error.detail || "Something went wrong.";
  }
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return "Something went wrong.";
}

export async function errorFromResponse(response: Response): Promise<ApiError> {
  let body: unknown = null;
  try {
    body = await response.json();
  } catch {
    body = null;
  }
  const record = body && typeof body === "object" ? (body as Record<string, unknown>) : {};
  const code = typeof record.error === "string" ? record.error : "error";
  const detail = typeof record.detail === "string" ? record.detail : "";
  const fields: Record<string, string[]> = {};
  if (record.fields && typeof record.fields === "object") {
    for (const [key, value] of Object.entries(record.fields as Record<string, unknown>)) {
      if (Array.isArray(value)) {
        fields[key] = value.map((item) => String(item));
      } else if (typeof value === "string") {
        fields[key] = [value];
      }
    }
  }
  return new ApiError(response.status, code, detail, fields);
}
