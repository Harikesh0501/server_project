import axios, { AxiosInstance } from 'axios';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';

export interface DomainCheckResult {
  name: string;
  available: boolean;
  full_domain: string;
  message: string;
  suggestions: string[];
}

export class ApiClient {
  private client: AxiosInstance;
  private configPath: string;

  constructor() {
    this.configPath = path.join(os.homedir(), '.deployrc');
    const config = this.loadConfig();
    const baseURL = process.env.DEPLOY_API_URL || config.apiUrl || 'http://127.0.0.1:8000';

    this.client = axios.create({
      baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
        ...(config.token ? { Authorization: `Bearer ${config.token}` } : {})
      }
    });
  }

  private loadConfig(): { apiUrl?: string; token?: string } {
    try {
      if (fs.existsSync(this.configPath)) {
        return JSON.parse(fs.readFileSync(this.configPath, 'utf8'));
      }
    } catch {
      // Ignore config read error
    }
    return {};
  }

  public saveConfig(newConfig: { apiUrl?: string; token?: string }) {
    const existing = this.loadConfig();
    const updated = { ...existing, ...newConfig };
    fs.writeFileSync(this.configPath, JSON.stringify(updated, null, 2), 'utf8');
  }

  async getHealth() {
    const response = await this.client.get('/api/v1/health');
    return response.data;
  }

  async checkDomain(name: string): Promise<DomainCheckResult> {
    const response = await this.client.get<DomainCheckResult>('/api/v1/domains/check', {
      params: { name }
    });
    return response.data;
  }

  async listProjects() {
    const response = await this.client.get('/api/v1/projects');
    return response.data;
  }

  async createProject(payload: {
    name: string;
    subdomain?: string;
    framework?: string;
    runtime_type?: string;
    git_url?: string;
    git_branch?: string;
    port?: number;
  }) {
    const response = await this.client.post('/api/v1/projects', payload);
    return response.data;
  }
}

export const apiClient = new ApiClient();
