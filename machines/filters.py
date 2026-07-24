# Questo file definisce i filtri di ricerca usati dalle API dei macchinari.
import django_filters
from .models import Machine


class MachineFilter(django_filters.FilterSet):
    """Filtri rapidi per la tabella macchinari"""
    cdl = django_filters.CharFilter(lookup_expr='icontains')
    cc = django_filters.CharFilter(lookup_expr='icontains')
    capannone = django_filters.CharFilter(lookup_expr='icontains')
    anno_avviamento_min = django_filters.NumberFilter(field_name='anno_avviamento',
                                                       lookup_expr='gte')
    anno_avviamento_max = django_filters.NumberFilter(field_name='anno_avviamento',
                                                       lookup_expr='lte')

    class Meta:
        model = Machine
        fields = ['stato', 'capannone', 'cdl', 'cc']
