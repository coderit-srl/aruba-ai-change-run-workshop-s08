<!--
Fonte: PostgreSQL 15.19 Release Notes, https://www.postgresql.org/docs/release/15.19/
Estratto: le prime dodici voci della sezione "Changes", testo originale non modificato.
Copyright (c) 1996-2026, The PostgreSQL Global Development Group. Distribuito sotto la
PostgreSQL License, che ne consente la copia e la redistribuzione con questa nota.
-->

## E.1. Release 15.19
Release date: 2026-08-13

This release contains a variety of fixes from 15.18. For information about new features in major release 15, see Section E.20.

### E.1.1. Migration to Version 15.19

A dump/restore is not required for those running 15.X.

However, the first three security entries below describe configuration adjustments and data cleanups that you may need to make after updating.

Also, if you use `contrib/btree_gist` or `contrib/ltree`, you may need to reindex indexes made with those extensions; see the relevant entries below.

Also, if you are upgrading from a version earlier than 15.14, see Section E.6.

### E.1.2. Changes

- Restrict logical decoding output plugins to the set specified by a new server parameter `output_plugin_libraries` (Jacob Champion)

Previously, a replication user could select any loadable library for logical decoding, allowing exploits of various sorts. To allow locking this down without breaking setups that worked before, introduce a whitelist of allowed output plugins.

By default, only the output plugins shipped as part of PostgreSQL (`pgoutput` and `test_decoding`) are included in `output_plugin_libraries`. Installations that rely on other output plugins must add them after updating the server, for example

output_plugin_libraries = 'pgoutput, test_decoding, my_trusted_decoder'

Additionally, `pg_upgrade --check` will fail if the `output_plugin_libraries` parameter on the new cluster does not permit the plugins of logical replication slots on the old cluster, when migrating from versions 17 and later. Make necessary additions to the new cluster's setting before performing pg_upgrade.

The PostgreSQL Project thanks Vladimir Tokarev and Yu Kunpeng for reporting this problem. (CVE-2026-6471)

- Fix `contrib/pgcrypto`'s PGP encryption to detect unsupported ciphers (Daniel Gustafsson)

Previously, if OpenSSL rejected the requested cipher (for example, because it is running in FIPS mode, or the legacy provider hasn't been loaded), pgcrypto failed to notice the failure and simply XOR'd the non-encrypted block with the plaintext, rendering the “encryption” trivially breakable. This will typically occur with deprecated or non-FIPS cipher algorithms (cipher-algo=blowfish/bf, twofish, cast5, or 3des).

By default, pgcrypto will now fail to decrypt any messages that were affected in this way. To allow retrieval of such data, a new option `ignore-cipher-failure` has been added to `pgp_pub_decrypt()` and `pgp_sym_decrypt()`. Setting `ignore-cipher-failure=1` will restore their previous behavior, allowing the faulty encryption wrapper to be stripped off:

pgp_sym_decrypt(encrypted_column, `any key`, 'ignore-cipher-failure=1')

Once the affected messages are identified and stripped of their wrappers, they can then be re-encrypted with a modern algorithm. It is important however that the behavior of OpenSSL be the same as it was when the faulty messages were created: if the set of unsupported algorithms is not the same, this approach will not work. See the documentation for `ignore-cipher-failure`.

The PostgreSQL Project thanks Shishir Sharma for reporting this problem. (CVE-2026-14663)

- Fix psql to skip in-line data following a scripted `COPY ... FROM STDIN` command, even if the `COPY` fails before sending `PGRES_COPY_IN` (Tom Lane)

Previously, if a `COPY` command failed at startup (for instance, because the target table doesn't exist) psql would not realize that and would proceed to read the following in-line data as SQL commands. In the best case that's wrong and in the worst case it's a SQL-injection hazard. Teach psql to recognize syntactically-valid `COPY ... FROM STDIN` commands and to skip data on its own authority if the server doesn't respond with `PGRES_COPY_IN`.

While this fix is unlikely to affect any production SQL scripts, test scripts might intentionally exercise failing `COPY ... FROM STDIN` commands. Those will need to gain a `\.` data terminator line after each such command.

The PostgreSQL Project thanks Alexander Lakhin for reporting this problem. (CVE-2026-6464)

- Cross-check the output row type of a portal running `EXECUTE` or `FETCH` (Robert Haas)

`EXECUTE` and `FETCH` use two portals: an outer one for the statement itself, and an inner one running the query being executed on its behalf. It was previously possible to make the declared row types of the two portals diverge, leading to server memory disclosure and arbitrary code execution.

The PostgreSQL Project thanks Ben Morris (in collaboration with Claude and Anthropic Research) and Peter Geoghegan for reporting this problem. (CVE-2026-16239)

- Fix buffer overrun with long time zone abbreviation in `to_char()` (Tom Lane)

This can easily crash the server, and exploits leading to arbitrary code execution have been reported.

The PostgreSQL Project thanks Hcamael, Amjad Shahzad, Tan Zhen of AntAISecurityLab, Tomer Fichman, Zheng Yu, Amy Burnett (OpenAI Codex Security), Rick de Jager, Heewon Song, Sylvie Mayer, Aleksander Alekseev, and Hillai Ben Sasson for reporting this problem. (CVE-2026-14669)

- Fix buffer overrun in regexp match/split functions (Masahiko Sawada)

If passed invalidly-encoded data, these functions could write past the end of their conversion buffer.

The PostgreSQL Project thanks Francesco Verardi for reporting this problem. (CVE-2026-14664)

- Harden the `ascii()` function against invalid input (Michael Paquier)

By supplying invalidly-encoded input, this function could be coaxed to read and return a few bytes of data that it shouldn't. In assert-enabled builds, its assertions could be triggered too.

The PostgreSQL Project thanks Hcamael for reporting this problem. (CVE-2026-18024)

- Fix multirange type handling in `pg_restore_attribute_stats()` (OpenAI Security Research Team)

`pg_restore_attribute_stats()` treated multirange types just like their underlying range type. This works correctly for the bounds histogram, but it was wrong for all the other statistics kinds.

The PostgreSQL Project thanks Amy Burnett (OpenAI Codex Security) for reporting this problem. (CVE-2026-16238)

- Make `scalarineqsel()` check that a constant it expects to be of type `tid` actually is (Tom Lane)

This expectation will hold for all the built-in operators that use this estimator, but a maliciously-constructed operator could violate it, leading to a crash or server memory disclosure.

The PostgreSQL Project thanks Hcamael for reporting this problem. (CVE-2026-14668)

- Harden `tsvector` and `tsquery` code against overly long values (both individual lexemes and total vector/query length) (Tom Lane)

The documented limits were not enforced in all code paths.

The PostgreSQL Project thanks Yuhang Wu, Zhenpeng Lin, Zheng Yu, and Hcamael for reporting these problems. (CVE-2026-14662)

- Fix various places that mistakenly assumed they would not have to deal with more than `FUNC_MAX_ARGS` function arguments (Tom Lane)

Notably, the server's actual limit on the number of arguments to an aggregate function is `FUNC_MAX_ARGS - 1`, but the parser failed to enforce that, creating hazards downstream.

The PostgreSQL Project thanks Zheng Yu, ylwangtju, and Masahiko Sawada for reporting these problems. (CVE-2026-14679)

- Reject calls from SQL to functions that take or return type `internal` (Tom Lane)

The existing defenses against doing this have been shown to be insufficient, so add more explicit checks.

The PostgreSQL Project thanks Amy Burnett (OpenAI Codex Security) for reporting this problem. (CVE-2026-14680)
