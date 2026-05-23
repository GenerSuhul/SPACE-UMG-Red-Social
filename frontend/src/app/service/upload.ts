import { Injectable } from '@angular/core';
import { HttpClient, HttpEvent, HttpRequest } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Config } from './config/config';

@Injectable({ providedIn: 'root' })
export class UploadService {
  private readonly baseUrl: string;

  constructor(private http: HttpClient, private configService: Config) {
    this.baseUrl = `${this.configService.appConfig.apiUrl}/api/upload`;
  }

  /**
   * Uploads a file to the Cloudflare R2 endpoints with real-time progress reporting.
   */
  uploadFile(file: File, endpoint: 'avatar' | 'post' | 'reel' | 'story' | 'chat'): Observable<HttpEvent<any>> {
    const fd = new FormData();
    fd.append('file', file);

    const req = new HttpRequest('POST', `${this.baseUrl}/${endpoint}`, fd, {
      reportProgress: true,
      responseType: 'json'
    });

    return this.http.request(req);
  }
}
