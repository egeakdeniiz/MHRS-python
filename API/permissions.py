from rest_framework.permissions import BasePermission

from accounts.models import Rol


def rol_izni(*roller):
    class _RolIzni(BasePermission):
        message = "Bu işlem için yetkiniz yok."

        def has_permission(self, request, view):
            u = request.user
            if not (u and u.is_authenticated):
                return False
            if u.is_superuser:
                return True
            if u.rol not in roller:
                return False
            if u.rol == Rol.HASTANE_YONETICISI and not u.hastane_id:
                return False
            if u.rol == Rol.HEKIM and not hasattr(u, "hekim"):
                return False
            return True

    _RolIzni.__name__ = "RolIzni_" + "_".join(roller)
    return _RolIzni


VatandasIzni = rol_izni(Rol.VATANDAS)
HekimIzni = rol_izni(Rol.HEKIM)
HastaneYoneticisiIzni = rol_izni(Rol.HASTANE_YONETICISI)
YoneticiIzni = rol_izni(Rol.HASTANE_YONETICISI, Rol.SISTEM_YONETICISI)
