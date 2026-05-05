export interface UserInterface {
  username:   string;
  email:      string;
  age:        number;
  first_name: string;
  last_name:  string;
  is_active:  boolean;
}

export interface GetUserResponse {
  ok:   boolean;
  user: UserInterface;
}
