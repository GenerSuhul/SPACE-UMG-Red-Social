export type ReactionType = 'like' | 'love' | 'haha' | 'wow' | 'sad' | 'angry';

export interface ReactionsCount {
  like:  number;
  love:  number;
  haha:  number;
  wow:   number;
  sad:   number;
  angry: number;
}

export interface Post {
  id:                    string;
  author_id:             string;
  author_username:       string;
  author_avatar_base64:  string | null;
  author_avatar_mime:    string | null;
  content:               string;
  media_urls:            string[];
  image_base64:          string | null;
  image_mime:            string | null;
  created_at:            string;
  updated_at:            string | null;
  reactions_count:       ReactionsCount;
  comments_count:        number;
}

export interface Comment {
  id:                   string;
  post_id:              string;
  author_id:            string;
  author_username:      string;
  author_avatar_base64: string | null;
  author_avatar_mime:   string | null;
  content:              string;
  parent_comment_id:    string | null;
  image_base64:         string | null;
  image_mime:           string | null;
  created_at:           string;
  reactions_count:      ReactionsCount;
}

export interface Reaction {
  id:            string;
  user_id:       string;
  target_id:     string;
  target_type:   'post' | 'comment';
  reaction_type: ReactionType;
  created_at:    string;
}

export interface Pagination {
  page:        number;
  page_size:   number;
  total?:      number;
  total_pages?: number;
}

// ---- API response shapes ----

export interface ListPostsResponse {
  ok:         boolean;
  posts:      Post[];
  pagination: Pagination;
}

export interface GetPostResponse {
  ok:       boolean;
  post:     Post;
  comments: Comment[];
}

export interface ListCommentsResponse {
  ok:         boolean;
  comments:   Comment[];
  pagination: Pagination;
}

export interface ListRepliesResponse {
  ok:         boolean;
  replies:    Comment[];
  pagination: Pagination;
}

export interface CreatePostResponse {
  ok:   boolean;
  post: Post;
}

export interface CreateCommentResponse {
  ok:      boolean;
  comment: Comment;
}

export interface ReactionResponse {
  ok:       boolean;
  reaction: Reaction;
  action:   'created' | 'updated' | 'unchanged';
}

export interface DeleteResponse {
  ok:      boolean;
  message: string;
}
