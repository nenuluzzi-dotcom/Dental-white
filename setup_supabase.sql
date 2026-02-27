-- Ejecutar en Supabase → SQL Editor

CREATE TABLE IF NOT EXISTS cupones (
    id              BIGSERIAL PRIMARY KEY,
    cuenta          TEXT,
    nombre          TEXT,
    monto           REAL,
    cta             TEXT,
    mes             TEXT,
    telefono        TEXT,
    provincia       TEXT,
    estado          TEXT DEFAULT 'PENDIENTE',
    visto           INTEGER DEFAULT 0,
    fecha_pago      TEXT,
    img_path        TEXT,
    comentario      TEXT,
    fecha_cobro     TEXT,
    balance_inicial REAL,
    medio_pago      TEXT,
    listo           BOOLEAN DEFAULT FALSE
);

-- Índices para búsquedas rápidas
CREATE INDEX IF NOT EXISTS idx_provincia ON cupones(provincia);
CREATE INDEX IF NOT EXISTS idx_estado    ON cupones(estado);
CREATE INDEX IF NOT EXISTS idx_fecha_pago ON cupones(fecha_pago);
CREATE INDEX IF NOT EXISTS idx_cuenta    ON cupones(cuenta);

-- Permitir acceso desde la app (deshabilitar RLS para uso interno)
ALTER TABLE cupones DISABLE ROW LEVEL SECURITY;

-- Bucket para imágenes de cupones
INSERT INTO storage.buckets (id, name, public)
VALUES ('cupones', 'cupones', true)
ON CONFLICT DO NOTHING;
