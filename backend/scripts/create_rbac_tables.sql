-- 创建角色表
CREATE TABLE IF NOT EXISTS stock.roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 创建权限表
CREATE TABLE IF NOT EXISTS stock.permissions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    parent_id INTEGER REFERENCES stock.permissions(id) ON DELETE SET NULL,
    path VARCHAR(255),
    level INTEGER NOT NULL DEFAULT 0,
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_menu BOOLEAN NOT NULL DEFAULT FALSE,
    icon VARCHAR(50),
    component VARCHAR(255),
    route_path VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 创建用户角色关联表
CREATE TABLE IF NOT EXISTS stock.user_roles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES stock.users(id) ON DELETE CASCADE,
    role_id INTEGER NOT NULL REFERENCES stock.roles(id) ON DELETE CASCADE,
    UNIQUE(user_id, role_id)
);

-- 创建角色权限关联表
CREATE TABLE IF NOT EXISTS stock.role_permissions (
    id SERIAL PRIMARY KEY,
    role_id INTEGER NOT NULL REFERENCES stock.roles(id) ON DELETE CASCADE,
    permission_id INTEGER NOT NULL REFERENCES stock.permissions(id) ON DELETE CASCADE,
    UNIQUE(role_id, permission_id)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_permissions_parent_id ON stock.permissions(parent_id);
CREATE INDEX IF NOT EXISTS idx_permissions_path ON stock.permissions(path);
CREATE INDEX IF NOT EXISTS idx_permissions_code ON stock.permissions(code);
CREATE INDEX IF NOT EXISTS idx_user_roles_user_id ON stock.user_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_role_id ON stock.user_roles(role_id);
CREATE INDEX IF NOT EXISTS idx_role_permissions_role_id ON stock.role_permissions(role_id);
CREATE INDEX IF NOT EXISTS idx_role_permissions_permission_id ON stock.role_permissions(permission_id);

-- 插入默认角色
INSERT INTO stock.roles (name, description) 
VALUES 
('超级管理员', '系统超级管理员，拥有所有权限'),
('普通用户', '普通用户，拥有基本操作权限')
ON CONFLICT (name) DO NOTHING;

-- 插入基础权限
INSERT INTO stock.permissions (name, code, description, parent_id, path, level, sort_order, is_menu, icon, component, route_path) 
VALUES 
-- 系统管理
('系统管理', 'system', '系统管理相关功能', NULL, '1', 0, 1, TRUE, 'bi-gear', NULL, NULL),

-- 用户管理
('用户管理', 'system:user', '用户管理相关功能', 1, '1/2', 1, 1, TRUE, 'bi-people', 'views/system/User.vue', '/system/user'),
('查看用户', 'system:user:view', '查看用户列表', 2, '1/2/3', 2, 1, FALSE, NULL, NULL, NULL),
('添加用户', 'system:user:add', '添加新用户', 2, '1/2/4', 2, 2, FALSE, NULL, NULL, NULL),
('编辑用户', 'system:user:edit', '编辑用户信息', 2, '1/2/5', 2, 3, FALSE, NULL, NULL, NULL),
('删除用户', 'system:user:delete', '删除用户', 2, '1/2/6', 2, 4, FALSE, NULL, NULL, NULL),
('分配角色', 'system:user:assign', '为用户分配角色', 2, '1/2/7', 2, 5, FALSE, NULL, NULL, NULL),

-- 角色管理
('角色管理', 'system:role', '角色管理相关功能', 1, '1/8', 1, 2, TRUE, 'bi-person-badge', 'views/system/Role.vue', '/system/role'),
('查看角色', 'system:role:view', '查看角色列表', 8, '1/8/9', 2, 1, FALSE, NULL, NULL, NULL),
('添加角色', 'system:role:add', '添加新角色', 8, '1/8/10', 2, 2, FALSE, NULL, NULL, NULL),
('编辑角色', 'system:role:edit', '编辑角色信息', 8, '1/8/11', 2, 3, FALSE, NULL, NULL, NULL),
('删除角色', 'system:role:delete', '删除角色', 8, '1/8/12', 2, 4, FALSE, NULL, NULL, NULL),
('分配权限', 'system:role:assign', '为角色分配权限', 8, '1/8/13', 2, 5, FALSE, NULL, NULL, NULL),

-- 权限管理
('权限管理', 'system:permission', '权限管理相关功能', 1, '1/14', 1, 3, TRUE, 'bi-shield-lock', 'views/system/Permission.vue', '/system/permission'),
('查看权限', 'system:permission:view', '查看权限列表', 14, '1/14/15', 2, 1, FALSE, NULL, NULL, NULL),
('添加权限', 'system:permission:add', '添加新权限', 14, '1/14/16', 2, 2, FALSE, NULL, NULL, NULL),
('编辑权限', 'system:permission:edit', '编辑权限信息', 14, '1/14/17', 2, 3, FALSE, NULL, NULL, NULL),
('删除权限', 'system:permission:delete', '删除权限', 14, '1/14/18', 2, 4, FALSE, NULL, NULL, NULL)

ON CONFLICT (code) DO NOTHING;

-- 为超级管理员角色分配所有权限
INSERT INTO stock.role_permissions (role_id, permission_id)
SELECT 
    (SELECT id FROM stock.roles WHERE name = '超级管理员'),
    id
FROM 
    stock.permissions
ON CONFLICT (role_id, permission_id) DO NOTHING;

-- 为普通用户角色分配基本权限
INSERT INTO stock.role_permissions (role_id, permission_id)
SELECT 
    (SELECT id FROM stock.roles WHERE name = '普通用户'),
    id
FROM 
    stock.permissions
WHERE 
    code IN ('system:user:view')
ON CONFLICT (role_id, permission_id) DO NOTHING; 