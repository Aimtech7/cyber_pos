-- Seed Initial Admin User
-- Password is 'admin123' (hashed with bcrypt)
INSERT INTO users (
    username, 
    email, 
    password_hash, 
    full_name, 
    role, 
    is_active
) VALUES (
    'admin', 
    'admin@example.com', 
    '$2b$12$Md.7QbAPh3cl97DLbA6bqekk3f81HohjAmuQjycJ1PSc0ltj5fZUa', 
    'Admin User', 
    'ADMIN', 
    TRUE
) ON CONFLICT (email) DO NOTHING;
