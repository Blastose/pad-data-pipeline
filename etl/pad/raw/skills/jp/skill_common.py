import json
import os
from typing import Dict, List
from enum import Enum

from pad.raw.skills.skill_common import *
import pad.raw.skills.skill_common as base_skill_common

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
AWOSKILLS = json.load(open(os.path.join(__location__, "../../../storage_processor/awoken_skill.json")))

__all__ = list(filter(lambda x: not x.startswith('__'), dir(base_skill_common)))


def public(x):
    global __all__
    __all__.append(x.__name__)
    return x


@public
class JpBaseTextConverter(BaseTextConverter):
    """Contains code shared across AS and LS converters."""

    _ATTRS = {
        -9: 'ロックされた爆弾',
        -1: 'ランダム属性の',
        None: '火',
        0: '火',
        1: '水',
        2: '木',
        3: '光',
        4: '闇',
        5: '回復',
        6: 'お邪魔',
        7: '毒',
        8: '猛毒',
        9: '爆弾',
    }

    _TYPES = {
        0: '進化用',
        1: 'バランス',
        2: '体力',
        3: '回復',
        4: 'ドラゴン',
        5: '神',
        6: '攻撃',
        7: '悪魔',
        8: 'マシン',
        12: '覚醒用',
        14: '強化合成用',
        15: '売却用',
    }

    _AWAKENING_MAP = {x['pad_awakening_id']: x['name_jp'] for x in AWOSKILLS}
    _AWAKENING_MAP[0] = ''

    @property
    def ATTRIBUTES(self) -> Dict[int, str]:
        return self._ATTRS

    @property
    def TYPES(self) -> Dict[int, str]:
        return self._TYPES

    @property
    def AWAKENING_MAP(self) -> Dict[int, str]:
        return self._AWAKENING_MAP

    def all_stats(self, multiplier):
        return '全パラメータが{}倍'.format(multiplier)

    def hp(self):
        return 'HP'

    def atk(self):
        return 'ATK'

    def rcv(self):
        return 'RCV'

    def reduce_all_pct(self, shield_text):
        return '受けるダメージを{}%減少'.format(shield_text)

    def reduce_attr_pct(self, attr_text, shield_text):
        return '{}属性の敵から受けるダメージを{}%減少'.format(attr_text, shield_text)

    @staticmethod
    def concat_list(iterable):
        array = '、'.join([str(i) for i in iterable if i])

    @staticmethod
    def concat_list_and(iterable, conj='と'):
        arr = [str(i) for i in iterable if i]
        if len(arr) == 0:
            return ""
        elif len(arr) == 1:
            return arr[0]
        elif len(arr) == 2:
            return conj.join(arr)
        return "、".join(arr)

    @staticmethod
    def concat_list_semicolons(iterable):
        return '。'.join([str(i) for i in iterable if i])

    @staticmethod
    def big_number(n):
        if n == 0:
            return str(int(n // 1e0)) + ''
        elif n % 1e8 == 0:
            return str(int(n // 1e8)) + '億'
        elif n % 1e7 == 0:
            return str(int(n // 1e7)) + '千万'
        elif n % 1e4 == 0:
            return str(int(n // 1e4)) + '万'
        elif n % 1e3 == 0:
            return str(int(n // 1e3)) + '千'

        elif n < 1e4:
            return str(n)
        elif n < 1e8:
            return str(n)[:-4] + '万' + str(n)[-4:]
        else:
            return str(n)[:-8] + '億' + str(n)[-8:-4] + '万' + str(n)[-4:]

    ################################################
    #               Format Functions               #
    ################################################
    
    def attributes_format(self, attributes: List[int], sep: str = ', ') -> str:
        return sep.join([self.ATTRIBUTES[i] for i in attributes])

    def types_format(self, types: List[int]) -> str:
        return ', '.join([self.TYPES[i] for i in types])

    def fmt_stats_type_attr_bonus(self, ls,
                                  reduce_join_txt='; ',
                                  skip_attr_all=True,
                                  atk=None,
                                  rcv=None,
                                  types=None,
                                  attributes=None,
                                  hp=None,
                                  shield=None,
                                  reduction_attributes=None):
        types = types or getattr(ls, 'types', [])
        attributes = attributes or getattr(ls, 'attributes', [])
        hp_mult = hp or getattr(ls, 'hp', 1)
        # TODO: maybe we can just move min_atk and min_rcv in here
        # TODO: had to add all these getattr because this is being used in the active
        #       skill parser as well, is this right?
        atk_mult = atk or getattr(ls, 'atk', 1)
        rcv_mult = rcv or getattr(ls, 'rcv', 1)
        damage_reduct = shield or getattr(ls, 'shield', 0)
        reduct_att = reduction_attributes or getattr(ls, 'reduction_attributes', [])

        skill_text = ''

        multiplier_text = self.fmt_multiplier_text(hp_mult, atk_mult, rcv_mult)
        if multiplier_text:
            skill_text += multiplier_text

            for_skill_text = ''
            if types:
                for_skill_text += ' {} type'.format(self.types_format(types))

            is_attr_all = len(attributes) in [0, 5]
            should_skip_attr = is_attr_all and skip_attr_all

            if attributes and not should_skip_attr:
                if for_skill_text:
                    for_skill_text += ' and'
                color_text = 'all' if len(attributes) == 5 else self.attributes_format(attributes)
                for_skill_text += ' ' + color_text + ' Att.'

            if for_skill_text:
                skill_text += ' for' + for_skill_text

        reduct_text = self.fmt_reduct_text(damage_reduct, reduct_att)
        if reduct_text:
            if multiplier_text:
                skill_text += reduce_join_txt
            if not skill_text or ';' in reduce_join_txt:
                reduct_text = reduct_text.capitalize()
            skill_text += reduct_text

        return skill_text

    def fmt_multi_attr(self, attributes, conj='or'):
        prefix = ''
        if 1 <= len(attributes) <= 7:
            attr_list = [self.ATTRIBUTES[i] for i in attributes]
        elif 7 <= len(attributes) < 10:
            # TODO: this is kind of weird maybe needs fixing
            # All the attributes except the duplicate 'None' for fire, random, locked bomb, etc
            non_attrs = [x for x in self.ATTRIBUTES.keys() if x is not None and x >= 0]
            attrs = list(set(non_attrs) - set(attributes))
            att_sym_diff = sorted(attrs, key=lambda x: self.ATTRIBUTES[x])
            attr_list = [self.ATTRIBUTES[i] for i in att_sym_diff]
            prefix = 'non '
        else:
            return '' if conj == 'or' else ' all'

        return prefix + self.concat_list_and(attr_list, conj)

    def fmt_multiplier_text(self, hp_mult, atk_mult, rcv_mult):
        if hp_mult == atk_mult and atk_mult == rcv_mult:
            if hp_mult == 1:
                return ''
            return self.all_stats(fmt_mult(hp_mult))

        mults = [(self.hp(), hp_mult), (self.atk(), atk_mult), (self.rcv(), rcv_mult)]
        mults = list(filter(lambda x: x[1] != 1, mults))
        mults.sort(key=lambda x: x[1], reverse=True)

        chunks = []
        x = 0
        while x < len(mults):
            can_check_double = x + 1 < len(mults)
            if can_check_double and mults[x][1] == mults[x + 1][1]:
                chunks.append(('{} & {}'.format(mults[x][0], mults[x + 1][0]), mults[x][1]))
                x += 2
            else:
                chunks.append((mults[x][0], mults[x][1]))
                x += 1

        output = ''
        for c in chunks:
            if len(output):
                output += ' and '
            output += '{}x {}'.format(fmt_mult(c[1]), c[0])

        return output

    def fmt_reduct_text(self, shield, reduct_att=None):
        if shield == 0:
            return ''
        shield_text = fmt_mult(shield * 100)
        if reduct_att in [None, [], [0, 1, 2, 3, 4]]:
            return self.reduce_all_pct(shield_text)
        else:
            color_text = self.attributes_format(reduct_att)
            return self.reduce_attr_pct(color_text, shield_text)

