import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, tap } from 'rxjs';
import { Config } from '../config/config';
import {
  FollowToggleResponse,
  GetPublicUserResponse,
  GetUserResponse,
  MyFollowsResponse,
  SearchUsersResponse,
  UpdateAvatarResponse,
  UserInterface,
} from '../../models/users';

@Injectable({ providedIn: 'root' })
export class UsersService {
  private readonly currentUserSubject = new BehaviorSubject<UserInterface | null>(null);

  /** Emits the latest loaded user. Subscribe in toolbar / any component needing user state. */
  readonly currentUser$ = this.currentUserSubject.asObservable();

  constructor(private http: HttpClient, private configService: Config) {}

  getUser(): Observable<GetUserResponse> {
    const url = `${this.configService.appConfig.apiUrl}/api/users/get_user`;
    return this.http.get<GetUserResponse>(url).pipe(
      tap(res => {
        if (res.ok) this.currentUserSubject.next(res.user);
      }),
    );
  }

  /** Existing JSON-body update — kept for backward compatibility. */
  updateUser(data: Partial<UserInterface>): Observable<GetUserResponse> {
    const url = `${this.configService.appConfig.apiUrl}/api/users/update_me`;
    return this.http.patch<GetUserResponse>(url, data).pipe(
      tap(res => {
        if (res.ok) this.currentUserSubject.next(res.user);
      }),
    );
  }

  /** Upload a new avatar image via multipart/form-data. */
  updateAvatar(file: File): Observable<UpdateAvatarResponse> {
    const url = `${this.configService.appConfig.apiUrl}/api/users/update_me`;
    const fd = new FormData();
    fd.append('avatar', file);
    return this.http.patch<UpdateAvatarResponse>(url, fd).pipe(
      tap(res => {
        if (res.ok) this.currentUserSubject.next(res.user);
      }),
    );
  }

  /** Combined update: profile fields + optional avatar, all in one multipart request. */
  updateProfile(
    data: Partial<Omit<UserInterface, 'avatar_base64' | 'avatar_mime'>>,
    file?: File,
  ): Observable<UpdateAvatarResponse> {
    const url = `${this.configService.appConfig.apiUrl}/api/users/update_me`;
    const fd = new FormData();
    (Object.entries(data) as [string, unknown][]).forEach(([k, v]) => {
      if (v !== undefined && v !== null) fd.append(k, String(v));
    });
    if (file) fd.append('avatar', file);
    return this.http.patch<UpdateAvatarResponse>(url, fd).pipe(
      tap(res => {
        if (res.ok) this.currentUserSubject.next(res.user);
      }),
    );
  }

  /** Search users by username (debounced at the call site). */
  searchUsers(query: string, limit = 20): Observable<SearchUsersResponse> {
    const url    = `${this.configService.appConfig.apiUrl}/api/users/search`;
    const params = { q: query, limit: String(limit) };
    return this.http.get<SearchUsersResponse>(url, { params });
  }

  /** Fetch the public profile of any user by their id. */
  getUserById(userId: string): Observable<GetPublicUserResponse> {
    const url = `${this.configService.appConfig.apiUrl}/api/users/${userId}`;
    return this.http.get<GetPublicUserResponse>(url);
  }

  /** Fetch the authenticated user's full followers and following lists. */
  getMyFollows(): Observable<MyFollowsResponse> {
    const url = `${this.configService.appConfig.apiUrl}/api/users/me/follows`;
    return this.http.get<MyFollowsResponse>(url);
  }

  /** Toggle follow/unfollow for any user by id. */
  toggleFollow(targetUserId: string): Observable<FollowToggleResponse> {
    const url = `${this.configService.appConfig.apiUrl}/api/users/follow/${targetUserId}`;
    return this.http.post<FollowToggleResponse>(url, {});
  }

  /** Imperatively push a user update (e.g. after local edits). */
  setCurrentUser(user: UserInterface): void {
    this.currentUserSubject.next(user);
  }
}
