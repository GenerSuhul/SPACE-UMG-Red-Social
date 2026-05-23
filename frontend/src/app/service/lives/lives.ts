import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { Config } from '../config/config';

@Injectable({ providedIn: 'root' })
export class LivesService {

  constructor(private http: HttpClient, private configService: Config) {}

  /** Start a simulated live stream. */
  startLive(title: string): Observable<any> {
    const url = `${this.configService.appConfig.apiUrl}/api/lives/`;
    return this.http.post<any>(url, { title });
  }

  /** List all active live streams. */
  listActiveLives(): Observable<any> {
    const url = `${this.configService.appConfig.apiUrl}/api/lives/`;
    return this.http.get<any>(url);
  }

  /** End a live stream. */
  endLive(streamId: string): Observable<any> {
    const url = `${this.configService.appConfig.apiUrl}/api/lives/${streamId}/end`;
    return this.http.post<any>(url, {});
  }

  /** Send a heartbeat to maintain the live active and fetch simulation updates. */
  sendHeartbeat(streamId: string): Observable<any> {
    const url = `${this.configService.appConfig.apiUrl}/api/lives/${streamId}/heartbeat`;
    return this.http.post<any>(url, {});
  }
}
