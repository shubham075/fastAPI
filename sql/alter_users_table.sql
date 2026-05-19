ALTER TABLE users
ADD
    first_name NVARCHAR(100) NULL,
    last_name NVARCHAR(100) NULL,
    mobile NVARCHAR(20) NULL,
    password_hash NVARCHAR(255) NULL,
    date_of_birth DATE NULL,
    gender NVARCHAR(20) NULL,
    is_active BIT NOT NULL CONSTRAINT DF_users_is_active DEFAULT 1,
    role NVARCHAR(50) NOT NULL CONSTRAINT DF_users_role DEFAULT 'user',
    created_at DATETIME2 NOT NULL CONSTRAINT DF_users_created_at DEFAULT SYSUTCDATETIME(),
    updated_at DATETIME2 NOT NULL CONSTRAINT DF_users_updated_at DEFAULT SYSUTCDATETIME();

UPDATE users
SET
    first_name = COALESCE(first_name, name),
    last_name = COALESCE(last_name, ''),
    mobile = COALESCE(NULLIF(mobile, ''), CONCAT('pending-', id)),
    password_hash = COALESCE(NULLIF(password_hash, ''), CONCAT('legacy-password-reset-', id)),
    date_of_birth = COALESCE(date_of_birth, '1900-01-01'),
    gender = COALESCE(gender, 'not_specified');

ALTER TABLE users ALTER COLUMN first_name NVARCHAR(100) NOT NULL;
ALTER TABLE users ALTER COLUMN last_name NVARCHAR(100) NOT NULL;
ALTER TABLE users ALTER COLUMN mobile NVARCHAR(20) NOT NULL;
ALTER TABLE users ALTER COLUMN password_hash NVARCHAR(255) NOT NULL;
ALTER TABLE users ALTER COLUMN date_of_birth DATE NOT NULL;
ALTER TABLE users ALTER COLUMN gender NVARCHAR(20) NOT NULL;

ALTER TABLE users DROP COLUMN name;

CREATE UNIQUE INDEX IX_users_mobile ON users(mobile);
