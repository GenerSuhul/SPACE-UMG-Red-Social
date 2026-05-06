export interface UserInterface {
  username:      string;
  email:         string;
  age:           number;
  first_name:    string;
  last_name:     string;
  is_active:     boolean;
  avatar_base64: string | null;
  avatar_mime:   string | null;
}

export interface GetUserResponse {
  ok:   boolean;
  user: UserInterface;
}

export interface UpdateAvatarResponse {
  ok:   boolean;
  user: UserInterface;
}
