# RCM1 canonical curation-metadata proposal

PPR1 obtained upstream acquisition/reference-method statements. PSH1 is closed at its first TLS validation failure with0body bytes and will not be retried or routed through another channel.

A different concrete source is identified by the already acquired pinned RegX README: it says the complete canonical regx_multiview_samples_v2.json includes curation metadata, whereas the acquired JSONL contains only the samples array. The existing complete pinned catalog identifies the canonical file as14,219,350bytes/Git blob f8fdfe31275f632bdb6bf97be1375662182db258. It has not been acquired by this work. The catalog's only executable source file is the already read viewer; no extraction-builder source path was found in that pinned catalog. This is not a global absence claim.

The proposed task is to acquire only this exact pinned JSON, verify its existing published identity, and inspect source/curation fields. It may answer an extraction question that samples-only metadata cannot. It also may leave the crosswalk unknown; a file named canonical is not assumed to contain independent physical evidence.

Because the file contains reference transforms, the proposed read boundary is explicit: acquire bytes and parse all numbers as strings, without converting them to floats, matrices or poses; do not compute errors or select cases by outcome/reference values. Report only root field names, source/curation descriptions and source-membership fields for the existing paris_02 scene. Existing exposed records retain that role.

REQUEST_PLAN.json fixes one14.219MB logical object, four total requests,16MiB delivered-body/32MiB dossier/180s transport/256MiB worker limits and unchanged fresh12GiB/2s host admission. Redirects are limited to the exact pinned HF resolve/resolve-cache paths, without another host or file. No raw/point/weight/code acquisition, credentials, scripts, API discovery, inference, training, metrics or outreach. This is a distinct source proposal, not a retry of the failed share request or an old-cap increase. Exact owner authorization is required by the existing source dependency.
