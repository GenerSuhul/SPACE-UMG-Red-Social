import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { Config } from '../config/config';

@Injectable({ providedIn: 'root' })
export class ChatsService {

  constructor(private http: HttpClient, private configService: Config) {}

  /** Start or fetch chat thread. */
  getOrCreateChat(otherUserId: string): Observable<any> {
    const url = `${this.configService.appConfig.apiUrl}/api/chats/`;
    return this.http.post<any>(url, { other_user_id: otherUserId });
  }

  /** List user's chats. */
  listMyChats(): Observable<any> {
    const url = `${this.configService.appConfig.apiUrl}/api/chats/`;
    return this.http.get<any>(url);
  }

  /** Get messages. */
  listMessages(chatId: string, limit = 50, page = 1): Observable<any> {
    const url = `${this.configService.appConfig.apiUrl}/api/chats/${chatId}/messages`;
    const params = { limit: String(limit), page: String(page) };
    return this.http.get<any>(url, { params });
  }

  /** Send message with optional media attachments. */
  sendMessage(chatId: string, content: string, mediaUrl?: string, mediaType?: string): Observable<any> {
    const url = `${this.configService.appConfig.apiUrl}/api/chats/${chatId}/messages`;
    const body: any = { content };
    if (mediaUrl) body.media_url = mediaUrl;
    if (mediaType) body.media_type = mediaType;
    return this.http.post<any>(url, body);
  }

  /** Mark chat as read. */
  markRead(chatId: string): Observable<any> {
    const url = `${this.configService.appConfig.apiUrl}/api/chats/${chatId}/read`;
    return this.http.post<any>(url, {});
  }
}
