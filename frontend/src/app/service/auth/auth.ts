import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { UserRegisterInterface } from '../../models/auth';
import { Observable } from 'rxjs';
import { Config } from '../config/config';

@Injectable({
  providedIn: 'root',
})
export class Auth {
  constructor(
    private http: HttpClient,
    private configService: Config
  ) {

  }

  registerUser(userRegister: UserRegisterInterface): Observable<any> {
    const url = `${this.configService.appConfig.apiUrl}/auth/register`
    return this.http.post<any>(url, userRegister);
  }
}
