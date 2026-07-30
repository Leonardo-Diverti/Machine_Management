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
    id_investimento_rm = django_filters.NumberFilter()
    id_investimento_consulente = django_filters.NumberFilter()
    consulente = django_filters.CharFilter(lookup_expr='icontains')
    interconnessione_stato = django_filters.CharFilter()

    class Meta:
        model = Machine
        fields = ['stato', 'capannone', 'stabilimento', 'cdl', 'cc', 'interconnessione_stato',
                  'id_investimento_rm', 'id_investimento_consulente', 'consulente', 'anno_avviamento']

