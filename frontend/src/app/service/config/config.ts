import { Injectable } from '@angular/core';
import { environment } from '../../../environment/environment';

@Injectable({
  providedIn: 'root',
})
export class Config {
  public appConfig: any;

  constructor() {
    this.appConfig = {
      server: environment.server,
      apiUrl: environment.server + environment.apiUrl
    }
  }
}
