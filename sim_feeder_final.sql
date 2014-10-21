select
	concat(b.nameFirst," ",b.nameLast) AS name,
	a.resp_bat_ID AS retroid,
	sum(if(a.event_cd=16,1,0))/count(a.event_cd) AS hbp_pct,
	sum(if(a.event_cd<>16,1,0))/count(a.event_cd) AS nonhbp_pct,
	sum(if(a.event_cd=3 OR a.event_cd=14 OR a.event_cd=15,1,0))/sum(if(a.event_cd<>16,1,0)) AS noncontact_per_nonhbp_pct,
	sum(if(a.event_cd<>3 AND a.event_cd<>14 AND a.event_cd<>15,1,0))/sum(if(a.event_cd<>16,1,0)) AS contact_per_nonhbp_pct,
	sum(if(a.event_cd=3,1,0))/sum(if(a.event_cd=3 or a.event_cd=14,1,0)) AS K_per_noncontact_pct,
	sum(if(a.event_cd=14,1,0))/sum(if(a.event_cd=3 or a.event_cd=14,1,0)) AS bb_per_noncontact_pct,
	sum(if(a.battedball_cd='G',1,0))/sum(if(a.battedball_cd<>'',1,0)) AS onground_per_contact_pct,
	sum(if(a.battedball_cd<>'G' and a.battedball_cd<>'',1,0))/sum(if(a.battedball_cd<>'',1,0)) AS inair_per_contact_pct,
	sum(if(a.battedball_cd='P',1,0))/sum(if(a.battedball_cd<>'' and a.battedball_cd<>'G',1,0)) AS iffb_per_inair_pct,
	sum(if(a.battedball_cd='L' or a.battedball_cd='F',1,0))/sum(if(a.battedball_cd<>'' and a.battedball_cd<>'G',1,0)) AS noniffb_per_inair_pct,
	sum(if(a.event_cd=23 AND (a.battedball_cd='F' OR a.battedball_cd='L'),1,0))/sum(if(a.battedball_cd='F' or a.battedball_cd='L',1,0)) AS hr_per_noniffb_pct,
	sum(if(a.event_cd<>23 AND (a.battedball_cd='F' OR a.battedball_cd='L'),1,0))/sum(if(a.battedball_cd='F' or a.battedball_cd='L',1,0)) AS nonhr_per_noniffb_pct,
	sum(if(a.battedball_cd='L' AND a.event_cd<>23,1,0))/sum(if(a.event_cd<>23 AND (a.battedball_cd='L' OR a.battedball_cd='F'),1,0)) AS ld_per_nonhr_pct,
	sum(if(a.battedball_cd='F' AND a.event_cd<>23,1,0))/sum(if(a.event_cd<>23 AND (a.battedball_cd='L' OR a.battedball_cd='F'),1,0)) AS fb_per_nonhr_pct,
	sum(if(a.event_cd<20 AND a.battedball_cd='L',1,0))/sum(if(a.battedball_cd='L' AND a.event_cd<>23,1,0)) AS out_per_ld_pct,
	sum(if(a.event_cd>19 AND a.event_cd<23 AND a.battedball_cd='L',1,0))/sum(if(a.battedball_cd='L' AND a.event_cd<>23,1,0)) AS nonout_per_ld_pct,
	sum(if(a.event_cd=20 AND a.battedball_cd='L',1,0))/sum(if(a.event_cd>19 AND a.event_cd<23 AND a.battedball_cd='L',1,0)) AS single_per_nonoutl,
	sum(if((a.event_cd=21 or a.event_cd=22) AND a.battedball_cd='L',1,0))/sum(if(a.event_cd>19 AND a.event_cd<23 AND a.battedball_cd='L',1,0)) AS xb_per_nonoutl,
	sum(if(a.event_cd<20 AND a.battedball_cd='F',1,0))/sum(if(a.battedball_cd='F' AND a.event_cd<>23,1,0)) AS out_per_fb_pct,
	sum(if(a.event_cd>19 AND a.event_cd<23 AND a.battedball_cd='F',1,0))/sum(if(a.battedball_cd='F' AND a.event_cd<>23,1,0)) AS nonout_per_fb_pct,
	sum(if(a.event_cd=20 AND a.battedball_cd='F',1,0))/sum(if(a.event_cd>19 AND a.event_cd<23 AND a.battedball_cd='f',1,0)) AS single_per_nonoutf,
	sum(if((a.event_cd=21 or a.event_cd=22) AND a.battedball_cd='F',1,0))/sum(if(a.event_cd>19 AND a.event_cd<23 AND a.battedball_cd='F',1,0)) AS xb_per_nonoutf,
	sum(if(a.event_cd<20 AND a.battedball_cd='G',1,0))/sum(if(a.battedball_cd='G',1,0)) AS out_per_gb_pct,
	sum(if(a.event_cd>19 AND a.event_cd<23 AND a.battedball_cd='G',1,0))/sum(if(a.battedball_cd='G',1,0)) AS nonout_per_gb_pct,
	sum(if(a.event_cd=20 AND a.battedball_cd='G',1,0))/sum(if(a.event_cd>19 AND a.event_cd<23 AND a.battedball_cd='G',1,0)) AS single_per_nonoutg,
	sum(if((a.event_cd=21 or a.event_cd=22) AND a.battedball_cd='G',1,0))/sum(if(a.event_cd>19 AND a.event_cd<23 AND a.battedball_cd='G',1,0)) AS xb_per_nonoutg
from
	events_regseason a
	left join master_new_retro_ids b
	on a.resp_bat_id = b.retroid
where
	a.year_ID = 2013
	AND a.bat_event_fl="T"
	AND a.bunt_fl<>"T" AND a.foul_fl<>"T" AND a.event_cd<>15
group by retroid