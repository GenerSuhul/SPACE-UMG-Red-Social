import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { Config } from '../config/config';

@Injectable({ providedIn: 'root' })
export class NotificationsService {

  constructor(private http: HttpClient, private configService: Config) {}

  /** Fetch notifications. */
  listNotifications(limit = 20): Observable<any> {
    const url = `${this.configService.appConfig.apiUrl}/api/notifications/`;
    const params = { limit: String(limit) };
    return this.http.get<any>(url, { params });
  }

  /** Mark all notifications as read. */
  markAllRead(): Observable<any> {
    const url = `${this.configService.appConfig.apiUrl}/api/notifications/read`;
    return this.http.post<any>(url, {});
  }
}
