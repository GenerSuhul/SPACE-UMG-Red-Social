import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { Config } from '../config/config';
import { GetUserResponse, UserInterface } from '../../models/users';

@Injectable({ providedIn: 'root' })
export class UsersService {
  constructor(private http: HttpClient, private configService: Config) {}

  getUser(): Observable<GetUserResponse> {
    const url = `${this.configService.appConfig.apiUrl}/api/users/get_user`;
    return this.http.get<GetUserResponse>(url);
  }

  updateUser(data: UserInterface): Observable<any> {
    const url = `${this.configService.appConfig.apiUrl}/users/update_me`;
    return this.http.put<any>(url, data);
  }
}
