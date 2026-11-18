# NOTEBOOK 02 — PRE-EXPORT CONSISTENCY AUDIT (v2: duplicate-column merge fix)
import numpy as np
import pandas as pd
from functools import lru_cache

KEYS = ['user', 'window_workdays']
DURATIONS = [5, 10, 20, 30, 40, 50]
CHANNELS = ['E', 'U', 'H']
FLAGS = ['email_active', 'usb_active', 'http_active']
STATES = ['NONE', 'E', 'U', 'H', 'EU', 'EH', 'UH', 'EUH']
results = []

def test(label, function):
    try:
        detail = function()
        results.append((label, 'PASS', detail or ''))
        print('PASS |', label, (f'| {detail}' if detail else ''))
    except Exception as exc:
        results.append((label, 'FAIL', f'{type(exc).__name__}: {exc}'))
        print('FAIL |', label, '|', type(exc).__name__, str(exc)[:250])

def require(condition, detail):
    if not bool(condition):
        raise AssertionError(detail)

def unique(df, cols):
    require(not df.duplicated(cols).any(), f'Nonunique keys: {cols}')

def paired(left, right, cols=KEYS):
    unique(left, cols)
    unique(right, cols)
    a = pd.MultiIndex.from_frame(left[cols])
    b = pd.MultiIndex.from_frame(right[cols])
    require(len(a) == len(b) and a.difference(b).empty and b.difference(a).empty,
            f'Key mismatch: {len(a)} vs {len(b)}')

def equal_cols(left, right, pairs):
    merged = left[KEYS + [a for a, _ in pairs]].merge(
        right[KEYS + [b for _, b in pairs]], on=KEYS,
        how='outer', validate='one_to_one', indicator=True)
    require(merged['_merge'].eq('both').all(), 'Missing matching keys')
    for a, b in pairs:
        require(merged[a].eq(merged[b]).all(), f'{a} differs from {b}')

def data_scope():
    unique(user_profile, ['user'])
    unique(future_daily, ['user', 'day'])
    require(len(user_profile) == 3995, 'Expected 3995 benign baseline users')
    require(len(future_daily) == 387162, 'Future daily count changed')
    require(future_daily['user'].nunique() == 3737, 'Unexpected Future population')
    require(future_daily['day'].dt.dayofweek.lt(5).all(), 'Nonweekday in eligible daily data')
    for flag, count in zip(FLAGS, ['external_email_count','usb_copy_count','www_upload_count']):
        require(future_daily[flag].astype(bool).eq(future_daily[count].gt(0)).all(),
                f'Flag not equal positive channel count: {flag}')
    flags_per_user = future_daily.groupby('user')[FLAGS].max().sum(axis=1)
    profile_multi = set(user_profile.loc[user_profile['active_channel_count'].ge(2), 'user'])
    observed_multi = set(flags_per_user.loc[flags_per_user.ge(2)].index)
    require(profile_multi == observed_multi, 'Candidate users do not match daily activity')
    require(len(observed_multi) == 995, 'Unexpected multi-channel candidate count')
    return f'3995 baseline users; 3737 active Future; 995 multi-channel'

def window_arithmetic():
    counts = future_daily.groupby('user').size().rename('n')
    w = window_length_capacity.merge(counts, left_on='user', right_index=True, how='left', validate='many_to_one')
    unique(w, KEYS)
    require(len(w) == len(future_daily), 'All user-length pairs should equal eligible daily rows')
    require(w['n'].notna().all(), 'Unknown user in window capacity')
    require(w['window_workdays'].between(1, w['n']).all(), 'Invalid window length')
    require(w['eligible_windows'].eq(w['n']-w['window_workdays']+1).all(),
            'Wrong n-L+1 window count')
    expected_total = int((counts * (counts + 1) // 2).sum())
    require(w['eligible_windows'].sum() == expected_total == 20436421, 'Triangle sum mismatch')
    require(w['calendar_contiguous_windows'].add(w['cross_gap_windows']).eq(w['eligible_windows']).all(),
            'Calendar contiguous + cross gap does not equal eligible')
    return f'{len(w):,} user-length pairs; {expected_total:,} candidate windows'

def temporal_segments():
    unique(temporal_availability, ['user'])
    unique(calendar_segments, ['user', 'segment_id'])
    require(len(temporal_availability)==len(user_profile), 'Temporal population differs from baseline')
    a=temporal_availability.set_index('user')
    n=future_daily.groupby('user').size().reindex(a.index, fill_value=0)
    require(a['eligible_day_rows'].eq(n).all(), 'Temporal daily eligible counts differ from source')
    segment_n=calendar_segments.groupby('user')['segment_eligible_days'].sum().reindex(a.index,fill_value=0)
    require(segment_n.eq(n).all(), 'Calendar segment lengths do not cover all eligible days')
    segment_count=calendar_segments.groupby('user').size().reindex(a.index,fill_value=0)
    require(a['calendar_segment_count'].eq(segment_count).all(), 'Reported segment counts differ from segments')
    require(a.loc[n.gt(0),'longest_contiguous_eligible_run'].ge(1).all(), 'Invalid longest contiguous run for active users')
    require(a.loc[n.gt(0),'longest_contiguous_eligible_run'].le(n[n.gt(0)]).all(), 'Longest run exceeds eligible workdays')
    require(a.loc[n.gt(0),'calendar_coverage_pct'].between(0,100).all(), 'Calendar coverage outside [0,100] for active users')
    inactive_coverage = a.loc[n.eq(0),'calendar_coverage_pct']
    require((inactive_coverage.isna() | inactive_coverage.eq(0)).all(), 'Unexpected coverage for users without eligible workdays')
    return 'Temporal user counts and each calendar segment reconcile with source days'

def channel_partition():
    paired(window_length_capacity, channel_window_capacity)
    c = channel_window_capacity
    require(c[[f'windows_{s}' for s in STATES]].sum(axis=1).eq(c['eligible_windows']).all(),
            '8 channel states do not partition all windows')
    require(c['windows_one_observed_channel'].eq(c[['windows_E','windows_U','windows_H']].sum(axis=1)).all(),
            'One-channel partition wrong')
    require(c['windows_two_observed_channels'].eq(c[['windows_EU','windows_EH','windows_UH']].sum(axis=1)).all(),
            'Two-channel partition wrong')
    require(c['windows_three_observed_channels'].eq(c['windows_EUH']).all(),
            'Three-channel partition wrong')
    require(c['windows_2plus_observed_channels'].eq(c['windows_two_observed_channels']+c['windows_EUH']).all(),
            '2+ channel count wrong')
    require(c['windows_any_observed_channel'].eq(c['eligible_windows']-c['windows_NONE']).all(),
            'Any observed channel count wrong')
    return '8 channel states and all derived unions reconcile'

def distinct_order_exclusive():
    for t in (distinct_day_window_capacity, ordered_window_capacity, exclusive_order_capacity):
        paired(window_length_capacity, t)
    pairs = [
        ('distinct_day_2plus_windows','windows_any_ordered_pair'),
        ('distinct_day_three_windows','windows_three_distinct_order')]
    equal_cols(distinct_day_window_capacity, ordered_window_capacity, pairs)
    # The distinct-day table already carries the observed-channel
    # window counts. A direct merge with the channel table would create
    # _x/_y suffixes for these overlapping columns and cause KeyError.
    # Align by composite keys and explicitly verify source parity first.
    d = distinct_day_window_capacity.set_index(KEYS).sort_index()
    c = channel_window_capacity.set_index(KEYS).sort_index()
    for col in ('windows_2plus_observed_channels', 'windows_EUH'):
        require(col in d.columns and col in c.columns,
                f'Missing observed-channel support column: {col}')
        require(d[col].eq(c[col]).all(),
                f'Distinct-day observed support differs from channel audit: {col}')
    require(d['same_day_only_2plus_windows'].eq(
                d['windows_2plus_observed_channels'] - d['distinct_day_2plus_windows']).all(),
            'Same-day-only count mismatch')
    require(d['three_without_assignment_windows'].eq(
                d['windows_EUH'] - d['distinct_day_three_windows']).all(),
            'Three-channel unassignable count mismatch')
    require(d['three_pair_constraint_fail_windows'].le(
                d['three_without_assignment_windows']).all(),
            'Hall pair-constraint failures exceed unassignable windows')
    o = ordered_window_capacity
    require(o['windows_three_distinct_order'].le(o['windows_any_three_step_change']).all(),
            'Three-distinct > three-step union')
    require(o['windows_return_pattern'].le(o['windows_any_three_step_change']).all(),
            'Return > three-step union')
    ex = exclusive_order_capacity
    all_ordered = set(o.columns)
    for col in ex.columns:
        if not col.startswith('exclusive_'):
            continue
        suffix = col[len('exclusive_'):]
        counterpart = 'ordered_' + suffix
        if counterpart in all_ordered:
            equal_cols_subset = ex[KEYS+[col]].merge(o[KEYS+[counterpart]], on=KEYS, validate='one_to_one')
            require(equal_cols_subset[col].le(equal_cols_subset[counterpart]).all(),
                    f'Exclusive motif exceeds flexible: {suffix}')
    ex_o = ex[KEYS+['exclusive_any_ordered_pair']].merge(
        o[KEYS+['windows_any_ordered_pair']], on=KEYS, validate='one_to_one')
    require(ex_o['exclusive_any_ordered_pair'].le(ex_o['windows_any_ordered_pair']).all(),
            'Exclusive pair union exceeds flexible pair union')
    return 'Distinct-day, ordering, Hall conditions and exclusive subsets reconcile'

def recurrence_strength():
    paired(window_length_capacity, channel_recurrence_capacity)
    paired(window_length_capacity, window_support_strength)
    r = channel_recurrence_capacity
    require(r['windows_2plus_channels_each_3days'].le(r['windows_2plus_channels_each_2days']).all(),
            '2+ channel recurrence thresholds not nested')
    require(r['windows_3_channels_each_3days'].le(r['windows_3_channels_each_2days']).all(),
            'Three-channel recurrence thresholds not nested')
    require(r['windows_3_channels_each_2days'].le(r['windows_2plus_channels_each_2days']).all(),
            '3 channel recurrence > 2+ channel recurrence')
    p = window_support_strength
    pct_cols = [c for c in p if c.endswith('_pct')]
    require(bool(pct_cols), 'No support percentages found')
    require(p[pct_cols].notna().all().all(), 'Null support percentages')
    require(p[pct_cols].ge(0).all().all() and p[pct_cols].le(100+1e-8).all().all(),
            'Support percentages outside [0,100]')
    return f'{len(pct_cols)} percentage columns within 0–100%'

def long_rotation():
    unique(long_rotation_capacity, KEYS)
    expect = set(user_profile.loc[user_profile['active_channel_count'].ge(2),'user'])
    require(set(long_rotation_capacity['user']) == expect, 'Long rotation missing extra candidate users')
    joined = long_rotation_capacity.merge(window_length_capacity[KEYS+['eligible_windows']],
        on=KEYS, how='left', indicator=True, validate='one_to_one', suffixes=('_long','_main'))
    require(joined['_merge'].eq('both').all(), 'Long rotation missing user-length keys')
    require(joined['eligible_windows_long'].eq(joined['eligible_windows_main']).all(),
            'Long rotation window counts incorrect')
    q = long_rotation_capacity
    require(q['max_feasible_rotation_steps'].le(q['window_workdays']).all(),
            'Max rotation steps exceed window length')
    require(q['max_steps_using_3channels'].le(q['max_feasible_rotation_steps']).all(),
            'Max three-channel steps exceed any-channel steps')
    require((q['max_steps_using_3channels'].eq(0) | q['max_steps_using_3channels'].ge(3)).all(),
            'Three-channel max is neither zero nor 3+')
    for k in [2,3,4,5,6,8,10,15,20,30]:
        count = q[f'windows_supporting_{k}steps']
        require(count.between(0,q['eligible_windows']).all(), f'Invalid {k}-step support window count')
        require(count.gt(0).eq(q['max_feasible_rotation_steps'].ge(k)).all(),
                f'Best steps and count disagree at k={k}')
        if k>=3:
            z = q[f'windows_3channel_{k}steps']
            require(z.between(0,count).all(), f'Invalid three-channel support at {k}')
            require(z.gt(0).eq(q['max_steps_using_3channels'].ge(k)).all(),
                    f'Three-channel best and count disagree at {k}')
    return f'{len(q):,} multi-channel user-length rows valid'

def cadence_cross_checks():
    c=rotation_cadence_capacity
    k=KEYS+['minimum_interstep_offdays']
    unique(c,k)
    require(set(c['window_workdays']) == set(DURATIONS), 'Unexpected duration in cadence')
    require(set(c['minimum_interstep_offdays']) == {0,1,2}, 'Unexpected gap in cadence')
    subset=long_rotation_capacity[long_rotation_capacity['window_workdays'].isin(DURATIONS)]
    require(len(c)==3*len(subset), 'Missing user-duration-gap record')
    g0=c[c['minimum_interstep_offdays'].eq(0)]
    equal_cols(g0,subset,[
        ('maximum_rotation_steps','max_feasible_rotation_steps'),
        ('maximum_3channel_steps','max_steps_using_3channels'),
        ('windows_with_2plus_steps','windows_supporting_2steps'),
        ('windows_with_5plus_steps','windows_supporting_5steps'),
        ('windows_with_10plus_steps','windows_supporting_10steps'),
        ('windows_with_15plus_steps','windows_supporting_15steps'),
        ('windows_with_3channel_rotation','windows_3channel_3steps'),
        ('windows_with_3channel_5plus_steps','windows_3channel_5steps'),
        ('windows_with_3channel_10plus_steps','windows_3channel_10steps')])
    ceiling=(c['window_workdays']+c['minimum_interstep_offdays'])//(c['minimum_interstep_offdays']+1)
    require(c['maximum_rotation_steps'].le(ceiling).all(), 'Gap step ceiling violated')
    require(c['maximum_switches'].eq((c['maximum_rotation_steps']-1).clip(lower=0)).all(),
            'Switch count not steps-1')
    require(c['maximum_3channel_steps'].le(c['maximum_rotation_steps']).all(),
            'Three-channel steps exceed any-channel')
    require(c['unselected_days_at_user_best'].eq(c['window_workdays']-c['maximum_rotation_steps']).all(),
            'Unused days incorrect')
    require(c['windows_with_3channel_rotation'].le(c['windows_with_2plus_steps']).all(),
            'Three-channel window count exceeds any rotation count')
    for metric in ['maximum_rotation_steps','maximum_3channel_steps','windows_with_2plus_steps',
                   'windows_with_5plus_steps','windows_with_10plus_steps','windows_with_3channel_rotation']:
        wide=c.pivot(index=KEYS,columns='minimum_interstep_offdays',values=metric)
        require(wide[0].ge(wide[1]).all() and wide[1].ge(wide[2]).all(),
                f'Gap monotonicity failed for {metric}')
    return f'{len(c):,} duration/gap records and Gap-0 parity verified'

def detail_full_reconstruction():
    d=rotation_structure_detail
    unique(d,KEYS+['minimum_interstep_offdays','sequence_variant'])
    require(len(d[d['sequence_variant'].eq('maximum_rotation')])==len(rotation_cadence_capacity),
            'Missing main reconstructed sequence')
    require(set(d['sequence_variant'])=={'maximum_rotation','three_channel_alternative'},
            'Unknown sequence type')
    reference=rotation_cadence_capacity.set_index(KEYS+['minimum_interstep_offdays'])
    require(reference.index.is_unique,'Cadence reference duplicate keys')
    daily={u:g.sort_values('day').reset_index(drop=True)
           for u,g in future_daily.groupby('user',sort=False)}
    date_index={u:{pd.Timestamp(day):i for i,day in enumerate(g['day'])}
                for u,g in daily.items()}
    checked=0
    for r in d.itertuples(index=False):
        g=daily[r.user]
        start=date_index[r.user].get(pd.Timestamp(r.window_start))
        require(start is not None, f'Start date not found for {r.user}')
        L=int(r.window_workdays)
        win=g.iloc[start:start+L]
        require(len(win)==L and pd.Timestamp(win['day'].iloc[-1])==pd.Timestamp(r.window_end),
                f'Window boundaries mismatch for {r.user}')
        pos=np.fromstring(str(r.selected_day_positions),sep=',',dtype=np.int32)
        seq=str(r.sequence_pattern)
        require(len(pos)==len(seq)==int(r.rotation_steps), f'Path length mismatch for {r.user}')
        require(np.all((pos>=0)&(pos<L)) and np.all(np.diff(pos)>0),
                f'Invalid selected day positions for {r.user}')
        require(set(seq)<=set(CHANNELS),f'Unexpected channel letter {r.user}')
        ci=np.array([CHANNELS.index(x) for x in seq],dtype=np.int8)
        flags=win[FLAGS].to_numpy(dtype=np.int8)
        require(np.all(flags[pos,ci]==1),f'Inactive natural channel in path for {r.user}')
        require(np.all(ci[1:]!=ci[:-1]),f'Non-switching adjacent steps for {r.user}')
        gap=int(r.minimum_interstep_offdays)
        require(np.all(np.diff(pos)>=gap+1),f'Cadence violation in path for {r.user}')
        counts=np.bincount(ci,minlength=3)
        require([int(r.email_steps),int(r.usb_steps),int(r.http_steps)]==counts.tolist(),
                f'Channel step count mismatch for {r.user}')
        skips=np.diff(pos)-1
        lead=int(pos[0]); trail=L-1-int(pos[-1]); internal=int(skips.sum())
        require(int(r.total_unselected_days)==L-len(pos)==lead+internal+trail,
                f'Unused days mismatch for {r.user}')
        require((int(r.leading_unselected_days),int(r.internal_unselected_days),int(r.trailing_unselected_days))
                ==(lead,internal,trail), f'Gap distribution mismatch for {r.user}')
        require(int(r.channel_switches)==len(pos)-1, f'Switch count mismatch for {r.user}')
        require(np.isclose(float(r.dominant_channel_share),counts.max()/len(pos)),
                f'Dominant share mismatch for {r.user}')
        require(int(r.used_channel_count)==int(np.count_nonzero(counts)),
                f'Used channels mismatch for {r.user}')
        require(int(r.longest_internal_gap)==(int(skips.max()) if len(skips) else 0),
                f'Longest internal gap mismatch for {r.user}')
        require(np.isclose(float(r.median_internal_gap),np.median(skips) if len(skips) else 0),
                f'Median gap mismatch for {r.user}')
        transition_count={f'transitions_{a}_{b}':0 for a in CHANNELS for b in CHANNELS if a!=b}
        for a,b in zip(seq,seq[1:]):transition_count[f'transitions_{a}_{b}']+=1
        require(all(getattr(r,c)==v for c,v in transition_count.items()),
                f'Transition counts mismatch for {r.user}')
        require(int(r.distinct_transition_types)==sum(v>0 for v in transition_count.values()),
                f'Distinct transitions mismatch for {r.user}')
        if r.sequence_variant=='three_channel_alternative':
            require(len(set(seq))==3,f'Three-channel alternative missing channel for {r.user}')
        ref=reference.loc[(r.user,L,gap)]
        best=('maximum_rotation_steps' if r.sequence_variant=='maximum_rotation'
              else 'maximum_3channel_steps')
        require(len(pos)<=int(ref[best]),f'Path exceeds global optimum for {r.user}')
        require(int(r.global_best_steps)==int(ref[best]),f'Global best not matching reference for {r.user}')
        require(bool(r.matches_global_best)==(len(pos)==int(ref[best])),
                f'Global match indicator wrong for {r.user}')
        if gap==0 and r.sequence_variant=='maximum_rotation':
            require(len(pos)==int(ref[best]),f'Gap0 representative window not global best for {r.user}')
        checked+=1
    return f'{checked:,} paths checked against exact day/channel natural activity and arithmetic'

def summary_reconciliation():
    c=rotation_cadence_capacity
    summary=rotation_cadence_summary
    unique(summary,['window_workdays','minimum_interstep_offdays'])
    g=c.groupby(['window_workdays','minimum_interstep_offdays']).agg(
        users_with_windows=('user','nunique'),
        users_with_rotation=('maximum_rotation_steps',lambda x:int(x.ge(2).sum())),
        users_with_5plus_steps=('maximum_rotation_steps',lambda x:int(x.ge(5).sum())),
        users_with_10plus_steps=('maximum_rotation_steps',lambda x:int(x.ge(10).sum())),
        users_with_3channel_rotation=('maximum_3channel_steps',lambda x:int(x.ge(3).sum())),
        median_user_best_steps=('maximum_rotation_steps','median'),
        median_unselected_days_at_user_best=('unselected_days_at_user_best','median'),
        total_windows_with_rotation=('windows_with_2plus_steps','sum')
    ).reset_index()
    s=summary.merge(g,on=['window_workdays','minimum_interstep_offdays'],suffixes=('_saved','_recalc'),validate='one_to_one')
    require(len(s)==18,'Cadence summary has missing groups')
    for col in g.columns[2:]:
        require(np.allclose(s[col+'_saved'],s[col+'_recalc'],equal_nan=True),f'Cadence summary mismatch: {col}')
    d=rotation_structure_detail
    struct=rotation_structure_summary
    grp=d.groupby(['window_workdays','minimum_interstep_offdays','sequence_variant']).agg(
        users=('user','nunique'),median_steps=('rotation_steps','median'),
        users_using_three_channels=('used_channel_count',lambda x:int(x.eq(3).sum())),
        median_dominant_share=('dominant_channel_share','median'),
        median_internal_unselected=('internal_unselected_days','median'),
        median_longest_internal_gap=('longest_internal_gap','median'),
        users_matching_global_best=('matches_global_best','sum')).reset_index()
    j=struct.merge(grp,on=['window_workdays','minimum_interstep_offdays','sequence_variant'],
                   suffixes=('_saved','_recalc'),validate='one_to_one')
    require(len(j)==len(grp)==len(struct),'Structure summary missing a group')
    for col in grp.columns[3:]:
        require(np.allclose(j[col+'_saved'],j[col+'_recalc'],equal_nan=True),f'Structure summary mismatch: {col}')
    return f'{len(s)} cadence + {len(j)} structural summary groups re-aggregated'

def descriptive_summaries():
    bindings = [
        ('window_length_summary', 'window_length_capacity'),
        ('window_channel_summary', 'channel_window_capacity'),
        ('distinct_day_window_summary', 'distinct_day_window_capacity'),
        ('ordered_window_summary', 'ordered_window_capacity'),
        ('exclusive_order_summary', 'exclusive_order_capacity'),
        ('window_support_summary', 'window_support_strength'),
        ('channel_recurrence_summary', 'channel_recurrence_capacity'),
        ('long_rotation_summary', 'long_rotation_capacity')
    ]
    checked=0
    for summary_name, detail_name in bindings:
        summary=globals().get(summary_name)
        detail=globals().get(detail_name)
        if summary is None or detail is None:
            raise AssertionError(f'Missing in-memory table {summary_name} or {detail_name}')
        require('window_workdays' in summary and 'window_workdays' in detail,
                f'Window length missing in {summary_name}')
        unique(summary,['window_workdays'])
        require(set(summary['window_workdays'])==set(detail['window_workdays']),
                f'Window lengths differ: {summary_name}')
        require(summary['window_workdays'].between(1,108).all(),
                f'Invalid length: {summary_name}')
        checked+=1
    # This checks exact grouping domains and keys. Full mathematical
    # reaggregation of the complex summaries would require per-column formulas.
    return f'{checked} intermediate summary tables have complete, unique length domains'

@lru_cache(maxsize=None)
def brute_sequence(flags_tuple, gap):
    n=len(flags_tuple)
    BAD=-10000
    @lru_cache(None)
    def dfs(i,last,mask,cooldown):
        if i==n:
            return (0, 0 if mask==7 else BAD)
        aa,bb=dfs(i+1,last,mask,max(0,cooldown-1))
        if cooldown==0:
            for channel in range(3):
                if flags_tuple[i][channel] and channel!=last:
                    x,y=dfs(i+1,channel,mask | (1<<channel),gap)
                    aa=max(aa,1+x)
                    bb=max(bb,1+y)
        return aa,bb
    a,b=dfs(0,3,0,0)
    return a,max(0,b)

def independent_exhaustive_sample():
    # Independent exhaustive search: every skip/channel choice
    # on every small window for deterministic two- and three-channel users.
    peruser=future_daily.groupby('user')[FLAGS].max().sum(axis=1)
    two=sorted(peruser.index[peruser.eq(2)])[:3]
    three=sorted(peruser.index[peruser.eq(3)])[:3]
    selected=two+three
    c=rotation_cadence_capacity.set_index(KEYS+['minimum_interstep_offdays'])
    require(c.index.is_unique,'Duplicated cadence references')
    total=0
    for user in selected:
        f=future_daily.loc[future_daily['user'].eq(user)].sort_values('day')[FLAGS].to_numpy(dtype=np.int8)
        for L in (5,10):
            if L>len(f):continue
            for gap in (0,1,2):
                any_steps=[]; three_steps=[]
                for start in range(len(f)-L+1):
                    small=tuple(tuple(int(v) for v in row) for row in f[start:start+L])
                    a,b=brute_sequence(small,gap)
                    any_steps.append(a);three_steps.append(b)
                    total+=1
                ref=c.loc[(user,L,gap)]
                require(max(any_steps)==ref['maximum_rotation_steps'],f'Brute any mismatch {user}/{L}/{gap}')
                require(max(three_steps)==ref['maximum_3channel_steps'],f'Brute 3-channel mismatch {user}/{L}/{gap}')
                for k,col in [(2,'windows_with_2plus_steps'),(5,'windows_with_5plus_steps'),
                              (10,'windows_with_10plus_steps')]:
                    require(sum(v>=k for v in any_steps)==ref[col], f'Brute {col} mismatch {user}/{L}/{gap}')
                require(sum(v>=3 for v in three_steps)==ref['windows_with_3channel_rotation'],
                        f'Brute three-channel windows mismatch {user}/{L}/{gap}')
    return f'{total:,} windows exhaustively checked; {len(selected)} users, 3 gaps, lengths 5/10'

print('='*85)
print('NOTEBOOK 02 | PRE-EXPORT NUMERICAL + LOGICAL CONSISTENCY AUDIT')
print('='*85)
checks = [
    ('01 Scope / daily channel flags', data_scope),
    ('02 Temporal runs and calendar segments', temporal_segments),
    ('03 User-length windows / calendar partition', window_arithmetic),
    ('04 Exact channel-state partition', channel_partition),
    ('05 Distinct-day / ordered / exclusive support', distinct_order_exclusive),
    ('06 Recurrence / support percentages', recurrence_strength),
    ('07 Long-rotation support arithmetic', long_rotation),
    ('08 Gap 0 parity / cadence bounds and monotonicity', cadence_cross_checks),
    ('09 Every reconstructed path vs actual user-day flags', detail_full_reconstruction),
    ('10 Independent summary recalculation', summary_reconciliation),
    ('11 Intermediate summary grouping integrity', descriptive_summaries),
    ('12 Independent exhaustive small-window search', independent_exhaustive_sample),
]
for name,fn in checks:
    test(name,fn)

failed=[x for x in results if x[1]=='FAIL']
print('\n'+'='*85)
print(f'FINAL AUDIT: {len(results)-len(failed)}/{len(results)} PASSED')
if failed:
    print('STATUS: FAIL — DO NOT EXPORT OR SAVE ANY REPORTS')
    for name,_,reason in failed:
        print(' -',name,':',reason[:220])
else:
    print('STATUS: PASS — outputs internally consistent; injection feasibility NOT proven')
print('No files written. Baseline and source Future data unchanged.')
