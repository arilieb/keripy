# -*- encoding: utf-8 -*-
"""
tests.vdr.verifying module

"""

import pytest

from keri import kering
from keri.kering import Vrsn_1_0, Vrsn_2_0
from keri.app import habbing, signing
from keri.core import eventing as ceventing, scheming
from keri.core import parsing, coring, indexing
from keri.core.eventing import SealEvent
from keri.help import helping
from keri.vc import proving
from keri.vdr import verifying, credentialing, eventing


def test_verifier_query(mockHelpingNowUTC, mockCoringRandomNonce):
    with habbing.openHab(name="test", transferable=True, temp=True, salt=b'0123456789abcdef') as (hby, hab):
        regery = credentialing.Regery(hby=hby, name="test", temp=True)
        issuer = regery.makeRegistry(prefix=hab.pre, name="test")

        verfer = verifying.Verifier(hby=hby)
        msg = verfer.query(hab.pre, issuer.regk,
                           "EA8Ih8hxLi3mmkyItXK1u55cnHl4WgNZ_RE-gKXqgcX4",
                           route="tels")
        assert msg == (b'{"v":"KERI10JSON0000fe_","t":"qry","d":"EFa6oMZA5bgpALIc7yykT6O6'
                       b'ovdbDQnRFeTPDI4zaOhr","dt":"2021-01-01T00:00:00.000000+00:00","r'
                       b'":"tels","rr":"","q":{"i":"EA8Ih8hxLi3mmkyItXK1u55cnHl4WgNZ_RE-g'
                       b'KXqgcX4","ri":"EB-u4VAF7A7_GR8PXJoAVHv5X9vjtXew8Yo6Z3w9mQUQ"}}-V'
                       b'Aj-HABEMl4RhuR_JxpiMd1N8DEJEhTxM3Ovvn9Xya8AN-tiUbl-AABAABGnrnayV'
                       b'yK1siivaffGHpWWhcVThPN_dsePQvMXrlsOYNf0UdT0e6ch-0bN-UuOJCd1behue'
                       b'Zs_0V9FQ9vw0wK')


def test_verifier(seeder):
    with (habbing.openHab(name="sid", temp=True, salt=b'0123456789abcdef') as (hby, hab),
          habbing.openHab(name="recp", transferable=True, temp=True) as (recpHby, recp)):
        seeder.seedSchema(db=hby.db)
        seeder.seedSchema(db=recpHby.db)
        assert hab.pre == "EKC8085pwSwzLwUGzh-HrEoFDwZnCJq27bVp5atdMT9o"

        regery = credentialing.Regery(hby=hby, name="test", temp=True)
        issuer = regery.makeRegistry(prefix=hab.pre, name="test")
        rseal = SealEvent(issuer.regk, "0", issuer.regd)._asdict()
        hab.interact(data=[rseal])
        seqner = coring.Seqner(sn=hab.kever.sn)
        issuer.anchorMsg(pre=issuer.regk,
                         regd=issuer.regd,
                         seqner=seqner,
                         saider=coring.Saider(qb64=hab.kever.serder.said))
        regery.processEscrows()

        verifier = verifying.Verifier(hby=hby, reger=regery.reger)

        credSubject = dict(
            d="",
            i=recp.pre,
            dt=helping.nowIso8601(),
            LEI="254900OPPU84GM83MG36",
        )
        _, d = scheming.Saider.saidify(sad=credSubject, code=coring.MtrDex.Blake3_256, label=scheming.Saids.d)

        creder = proving.credential(issuer=hab.pre,
                                    schema="EMQWEcCnVRk1hatTNyK3sIykYSrrFvafX3bHQ9Gkk1kC",
                                    data=d,
                                    status=issuer.regk)
        missing = False
        try:
            # Specify an anchor directly in the KEL
            verifier.processCredential(creder, prefixer=hab.kever.prefixer, seqner=seqner,
                                       saider=coring.Saider(qb64=hab.kever.serder.said))
        except kering.MissingRegistryError:
            missing = True

        assert missing is True
        assert len(verifier.cues) == 1
        cue = verifier.cues.popleft()
        assert cue["kin"] == "telquery"
        q = cue["q"]
        assert q["ri"] == issuer.regk
        iss = issuer.issue(said=creder.said)
        rseal = SealEvent(iss.pre, "0", iss.said)._asdict()
        hab.interact(data=[rseal])
        seqner = coring.Seqner(sn=hab.kever.sn)
        issuer.anchorMsg(pre=iss.pre,
                         regd=iss.said,
                         seqner=seqner,
                         saider=coring.Saider(qb64=hab.kever.serder.said))
        regery.processEscrows()

        # Now that the credential has been issued, process escrows and it will find the TEL event
        verifier.processEscrows()

        assert len(verifier.cues) == 1
        cue = verifier.cues.popleft()
        assert cue["kin"] == "saved"
        assert cue["creder"].raw == creder.raw

        dcre, *_ = regery.reger.cloneCred(said=creder.said)

        assert dcre.raw == creder.raw

        saider = regery.reger.issus.get(hab.pre)
        assert saider[0].qb64 == creder.said
        saider = regery.reger.subjs.get(recp.pre)
        assert saider[0].qb64 == creder.said
        saider = regery.reger.schms.get("EMQWEcCnVRk1hatTNyK3sIykYSrrFvafX3bHQ9Gkk1kC")
        assert saider[0].qb64 == creder.said

        # also try it via the cloneCreds function
        creds = regery.reger.cloneCreds(saids=saider, db=hab.db)

        for cred in creds:
            assert dcre.sad == cred["sad"]
            assert cred['rev'] is None

        with pytest.raises(kering.MissingEntryError):
            regery.reger.cloneCred(said="nonexistantsaid")

    """End Test"""


# def test_verifier_multisig():
#     with test_grouping.openMutlsig(prefix="test") as ((hby1, hab1), (hby2, hab2), (hby3, hab3)), \
#             habbing.openHab(name="recp", transferable=True, temp=True) as (recpHab, recp), \
#             habbing.openHab(name="verfer", transferable=True, temp=True) as (verferHab, verfer), \
#             viring.openReg(temp=True) as reger:
#
#         gid = "Ea69OZWwWIVBvwX5a-LJjg8VAsc7sTL_OlxBHPdhKjow"
#         group1 = hab1.group()
#         assert group1.gid == gid
#
#         # Keverys so we can process the final message.
#         kev1 = ceventing.Kevery(db=hab1.db, lax=False, local=False)
#         kev2 = ceventing.Kevery(db=hab2.db, lax=False, local=False)
#         kev3 = ceventing.Kevery(db=hab3.db, lax=False, local=False)
#         vkev = ceventing.Kevery(db=verfer.db, lax=False, local=False)
#
#         micp = hab1.makeOtherEvent(gid, sn=0)
#         parsing.Parser(version=Vrsn_1_0).parse(ims=bytearray(micp), kvy=vkev)
#
#         g1 = grouping.Groupy(hby=hby1)
#         g2 = grouping.Groupy(hby=hby2)
#         g3 = grouping.Groupy(hby=hby3)
#
#         groupies = [g1, g2, g3]
#
#         issuer = credentialing.Issuer(hab=hab1, reger=reger, noBackers=True, estOnly=True, temp=True)
#         assert len(issuer.cues) == 1
#         cue = issuer.cues.popleft()
#         rseal = cue["data"]
#
#         imsg = dict(
#             op=grouping.Ops.ixn,
#             data=rseal,
#         )
#
#         for idx, groupy in enumerate(groupies):
#             missing = False
#             try:
#                 groupy.processMessage(imsg)
#             except kering.MissingSignatureError:
#                 missing = True
#             assert missing is True
#
#         raw = hab1.db.gpse.getLast(hab1.pre)
#         msg = json.loads(raw)
#         gid = msg["pre"]
#         dig = msg["dig"]
#
#         dgkey = dbing.dgKey(gid, dig)
#         eraw = hab1.db.getEvt(dgkey)
#         mssrdr = coring.Serder(raw=bytes(eraw))  # escrowed event
#
#         dgkey = dbing.dgKey(mssrdr.preb, mssrdr.saidb)
#         sigs = hab1.db.getSigs(dgkey)
#         sigs.extend(hab2.db.getSigs(dgkey))
#         sigs.extend(hab3.db.getSigs(dgkey))
#
#         sigers = [indexing.Siger(qb64b=bytes(sig)) for sig in sigs]
#
#         evt = bytearray(eraw)
#         evt.extend(coring.Counter(code=coring.CtrDex.ControllerIdxSigs,
#                                   count=len(sigers)).qb64b)  # attach cnt
#         for sig in sigs:
#             evt.extend(sig)
#
#         parsing.Parser(version=Vrsn_1_0).parse(ims=bytearray(evt), kvy=kev3)
#         parsing.Parser(version=Vrsn_1_0).parse(ims=bytearray(evt), kvy=kev2)
#         parsing.Parser(version=Vrsn_1_0).parse(ims=bytearray(evt), kvy=kev1)
#         parsing.Parser(version=Vrsn_1_0).parse(ims=bytearray(evt), kvy=vkev)
#
#         g1.processEscrows()
#         g2.processEscrows()
#         g3.processEscrows()
#
#         issuer.processEscrows()
#         assert issuer.regk in issuer.tevers
#
#         assert len(issuer.cues) == 1
#         cue = issuer.cues.popleft()
#         assert cue["kin"] == "logEvent"
#
#         verifier = verifying.Verifier(hab=verfer, reger=reger)
#
#         credSubject = dict(
#             d="",
#             i=recp.pre,
#             dt=helping.nowIso8601(),
#             LEI="254900OPPU84GM83MG36",
#         )
#         _, d = scheming.Saider.saidify(sad=credSubject, code=coring.MtrDex.Blake3_256, label=scheming.Ids.d)
#
#         creder = proving.credential(issuer=group1.gid,
#                                     schema="EIZPo6FxMZvZkX-463o9Og3a2NEKEJa-E9J5BXOsdpVg",
#                                     subject=d,
#                                     status=issuer.regk)
#
#         missing = False
#         try:
#             issuer.issue(creder)
#         except kering.MissingAnchorError:
#             missing = True
#         assert missing is True
#
#         assert len(issuer.cues) == 1
#         cue = issuer.cues.popleft()
#         rseal = cue["data"]
#
#         imsg = dict(
#             op=grouping.Ops.ixn,
#             data=rseal,
#         )
#
#         for idx, groupy in enumerate(groupies):
#             missing = False
#             try:
#                 groupy.processMessage(imsg)
#             except kering.MissingSignatureError:
#                 missing = True
#             assert missing is True
#
#         raw = hab1.db.gpse.getLast(hab1.pre)
#         msg = json.loads(raw)
#         gid = msg["pre"]
#         dig = msg["dig"]
#
#         dgkey = dbing.dgKey(gid, dig)
#         eraw = hab1.db.getEvt(dgkey)
#         mssrdr = coring.Serder(raw=bytes(eraw))  # escrowed event
#
#         dgkey = dbing.dgKey(mssrdr.preb, mssrdr.saidb)
#         sigs = hab1.db.getSigs(dgkey)
#         sigs.extend(hab2.db.getSigs(dgkey))
#         sigs.extend(hab3.db.getSigs(dgkey))
#
#         sigers = [indexing.Siger(qb64b=bytes(sig)) for sig in sigs]
#
#         evt = bytearray(eraw)
#         evt.extend(coring.Counter(code=coring.CtrDex.ControllerIdxSigs,
#                                   count=len(sigers)).qb64b)  # attach cnt
#         for sig in sigs:
#             evt.extend(sig)
#
#         parsing.Parser(version=Vrsn_1_0).parse(ims=bytearray(evt), kvy=kev3)
#         parsing.Parser(version=Vrsn_1_0).parse(ims=bytearray(evt), kvy=kev2)
#         parsing.Parser(version=Vrsn_1_0).parse(ims=bytearray(evt), kvy=kev1)
#         parsing.Parser(version=Vrsn_1_0).parse(ims=bytearray(evt), kvy=vkev)
#
#         g1.processEscrows()
#         g2.processEscrows()
#         g3.processEscrows()
#
#         kever = hab1.kevers[gid]
#         assert kever.sn == 2
#
#         issuer.processEscrows()
#         status = issuer.tvy.tevers[issuer.regk].vcState(creder.said)
#         assert status.ked["et"] == coring.Ilks.iss
#
#         gkev = hab1.kevers[gid]
#         prefixer = coring.Prefixer(qb64=gid)
#         seqner = coring.Seqner(sn=gkev.lastEst.s)
#         saider = coring.Saider(qb64=gkev.lastEst.d)
#
#         sigers = []
#         for idx, hab in enumerate([hab1, hab2, hab3]):
#             pather = coring.Pather(path=[])
#             data = pather.rawify(serder=creder)
#
#             sig = hab.sign(ser=data,
#                                verfers=hab.kever.verfers,
#                                indexed=True,
#                                indices=[idx])
#             sigers.extend(sig)
#
#         sadsigers = [(pather, prefixer, seqner, saider, sigers)]
#         verifier.processCredential(creder, sadsigers=sadsigers, sadcigars=[])
#
#         assert len(verifier.cues) == 1
#         cue = verifier.cues.popleft()
#         assert cue["kin"] == "saved"
#         assert cue["creder"].raw == creder.raw
#
#     """End Test"""


def test_verifier_chained_credential(seeder):
    qviSchema = "EFgnk_c08WmZGgv9_mpldibRuqFMTQN-rAgtD-TCOwbs"
    vLeiSchema = "ED892b40P_GcESs3wOcc2zFvL_GVi2Ybzp9isNTZKqP0"
    optionalIssueeSchema = "EAv8omZ-o3Pk45h72_WnIpt6LTWNzc8hmLjeblpxB9vz"

    with habbing.openHab(name="ron", temp=True, salt=b'0123456789abcdef') as (ronHby, ron), \
            habbing.openHab(name="ian", temp=True, salt=b'0123456789abcdef') as (ianHby, ian), \
            habbing.openHab(name="han", transferable=True, temp=True, salt=b'0123456789abcdef') as (hanHby, han), \
            habbing.openHab(name="vic", transferable=True, temp=True, salt=b'0123456789abcdef') as (vicHby, vic):
        seeder.seedSchema(db=ronHby.db)
        seeder.seedSchema(db=ianHby.db)
        seeder.seedSchema(db=hanHby.db)
        seeder.seedSchema(db=vicHby.db)

        assert ron.pre == "EOp2vZP2BrlH3DX9H3w-ghvr3c9kkDv0gS5ELFyutxwk"
        assert ian.pre == "EN6Ta5X_B7DrYR1HVGw25YgFVep4zGb5TMIoyCBaKb7R"
        assert han.pre == "EBwEKSIMG_3tp7kVCLWJ9c-tPdwtDXIeLlfdm5-IMTZv"
        assert vic.pre == "EGPhh6seaUvJy-nXFkiEdsfwekEhSm3lCVrP-tcoeL0H"

        ronreg = credentialing.Regery(hby=ronHby, name="ron", temp=True)
        ianreg = credentialing.Regery(hby=ianHby, name="ian", temp=True)
        vicreg = credentialing.Regery(hby=vicHby, name="vic", temp=True)
        roniss = ronreg.makeRegistry(prefix=ron.pre, name="test")
        rseal = SealEvent(roniss.regk, "0", roniss.regd)._asdict()
        ron.interact(data=[rseal])
        seqner = coring.Seqner(sn=ron.kever.sn)
        roniss.anchorMsg(pre=roniss.regk,
                         regd=roniss.regd,
                         seqner=seqner,
                         saider=coring.Saider(qb64=ron.kever.serder.said))
        ronreg.processEscrows()

        ronverfer = verifying.Verifier(hby=ronHby, reger=ronreg.reger)

        credSubject = dict(
            d="",
            i=ian.pre,
            dt=helping.nowIso8601(),
            LEI="5493001KJTIIGC8Y1R12",
        )
        _, d = scheming.Saider.saidify(sad=credSubject, code=coring.MtrDex.Blake3_256, label=scheming.Saids.d)

        creder = proving.credential(issuer=ron.pre,
                                    schema=qviSchema,
                                    data=d,
                                    status=roniss.regk)

        missing = False
        try:
            ronverfer.processCredential(creder, prefixer=ron.kever.prefixer, seqner=seqner,
                                        saider=coring.Saider(qb64=ron.kever.serder.said))
        except kering.MissingRegistryError:
            missing = True

        assert missing is True
        assert len(ronverfer.cues) == 1
        cue = ronverfer.cues.popleft()
        assert cue["kin"] == "telquery"
        q = cue["q"]
        assert q["ri"] == roniss.regk

        iss = roniss.issue(said=creder.said)
        rseal = SealEvent(iss.pre, "0", iss.said)._asdict()
        ron.interact(data=[rseal])
        seqner = coring.Seqner(sn=ron.kever.sn)
        roniss.anchorMsg(pre=iss.pre,
                         regd=iss.said,
                         seqner=seqner,
                         saider=coring.Saider(qb64=ron.kever.serder.said))
        ronreg.processEscrows()

        # Now that the credential has been issued, process escrows and it will find the TEL event
        ronverfer.processEscrows()

        assert len(ronverfer.cues) == 1
        cue = ronverfer.cues.popleft()
        assert cue["kin"] == "saved"
        assert cue["creder"].raw == creder.raw

        dcre, *_ = ronreg.reger.cloneCred(said=creder.said)
        assert dcre.raw == creder.raw

        saider = ronreg.reger.issus.get(ron.pre)
        assert saider[0].qb64 == creder.said
        saider = ronreg.reger.subjs.get(ian.pre)
        assert saider[0].qb64 == creder.said
        saider = ronreg.reger.schms.get(qviSchema)
        assert saider[0].qb64 == creder.said

        ianiss = ianreg.makeRegistry(prefix=ian.pre, name="ian")
        rseal = SealEvent(ianiss.regk, "0", ianiss.regd)._asdict()
        ian.interact(data=[rseal])
        seqner = coring.Seqner(sn=ian.kever.sn)
        ianiss.anchorMsg(pre=ianiss.regk,
                         regd=ianiss.regd,
                         seqner=seqner,
                         saider=coring.Saider(qb64=ian.kever.serder.said))
        ianreg.processEscrows()

        ianverfer = verifying.Verifier(hby=ianHby, reger=ianreg.reger)

        leiCredSubject = dict(
            d="",
            i=han.pre,
            dt=helping.nowIso8601(),
            LEI="254900OPPU84GM83MG36",
        )
        _, d = scheming.Saider.saidify(sad=leiCredSubject, code=coring.MtrDex.Blake3_256, label=scheming.Saids.d)

        chain = dict(
            d=creder.said,
            qualifiedvLEIIssuervLEICredential=dict(
                n=creder.said,
            ),
        )

        vLeiCreder = proving.credential(issuer=ian.pre,
                                        schema=vLeiSchema,
                                        data=d,
                                        status=ianiss.regk,
                                        source=chain,
                                        rules=[dict(
                                            usageDisclaimer="Use carefully."
                                        )])

        missing = False
        try:
            ianverfer.processCredential(vLeiCreder, prefixer=ian.kever.prefixer, seqner=seqner,
                                        saider=coring.Saider(qb64=ian.kever.serder.said))
        except kering.MissingRegistryError:
            missing = True

        assert missing is True
        assert len(ianverfer.cues) == 1
        cue = ianverfer.cues.popleft()
        assert cue["kin"] == "telquery"
        q = cue["q"]
        assert q["ri"] == ianiss.regk

        iss = ianiss.issue(said=vLeiCreder.said)
        rseal = SealEvent(iss.pre, "0", iss.said)._asdict()
        ian.interact(data=[rseal])
        seqner = coring.Seqner(sn=ian.kever.sn)
        ianiss.anchorMsg(pre=iss.pre,
                         regd=iss.said,
                         seqner=seqner,
                         saider=coring.Saider(qb64=ian.kever.serder.said))
        ianreg.processEscrows()

        # Now that the credential has been issued, process escrows and it will find the TEL event
        ianverfer.processEscrows()

        dcre, *_ = ianreg.reger.cloneCred(said=vLeiCreder.said)
        assert dcre.raw == vLeiCreder.raw

        dater = ianreg.reger.mce.get(vLeiCreder.saidb)
        assert dater is not None

        assert len(ianverfer.cues) == 1
        cue = ianverfer.cues.popleft()
        assert cue["kin"] == "proof"

        # Now lets get Ron's credential into Ian's Tevers and Database
        iankvy = ceventing.Kevery(db=ian.db, lax=False, local=False)
        iantvy = eventing.Tevery(reger=ianreg.reger, db=ian.db, local=False)
        ianverfer = verifying.Verifier(hby=ianHby, reger=ianreg.reger)

        # Now process all the events that Ron's issuer has generated so far
        for msg in ron.db.clonePreIter(pre=ron.pre):
            parsing.Parser(version=Vrsn_1_0).parse(ims=bytearray(msg), kvy=iankvy, tvy=iantvy)
        for msg in ronverfer.reger.clonePreIter(pre=roniss.regk):
            parsing.Parser(version=Vrsn_1_0).parse(ims=bytearray(msg), kvy=iankvy, tvy=iantvy)
        for msg in ronverfer.reger.clonePreIter(pre=creder.said):
            parsing.Parser(version=Vrsn_1_0).parse(ims=bytearray(msg), kvy=iankvy, tvy=iantvy)

        ianverfer.processCredential(creder, prefixer=ron.kever.prefixer, seqner=seqner,
                                    saider=coring.Saider(qb64=ron.kever.serder.said))

        # Process the escrows to get Ian's credential out of missing chain escrow
        ianverfer.processEscrows()

        # And now it should be in the indexes
        saider = ianreg.reger.issus.get(ian.pre)  # Ian is the issuer
        assert saider[0].qb64 == vLeiCreder.said
        saider = ianreg.reger.subjs.get(han.pre)  # Han is the holder
        assert saider[0].qb64 == vLeiCreder.said
        saider = ianreg.reger.schms.get(vLeiSchema)
        assert saider[0].qb64 == vLeiCreder.said

        # test operators

        untargetedSubject = dict(
            d="",
            dt=helping.nowIso8601(),
            claim="An outrageous claim.",
        )
        _, d = scheming.Saider.saidify(sad=untargetedSubject, code=coring.MtrDex.Blake3_256, label=scheming.Saids.d)

        chainSad = dict(
            d='',
            targetedEdge=dict(
                n=vLeiCreder.said,
            ),
        )
        _, chain = scheming.Saider.saidify(sad=chainSad, code=coring.MtrDex.Blake3_256, label=scheming.Saids.d)

        untargetedCreder = proving.credential(issuer=ian.pre,
                                              schema=optionalIssueeSchema,
                                              data=d,
                                              status=ianiss.regk,
                                              source=chain,
                                              rules={})

        missing = False
        try:
            ianverfer.processCredential(untargetedCreder, prefixer=ian.kever.prefixer, seqner=seqner,
                                        saider=coring.Saider(qb64=ian.kever.serder.said))
        except kering.MissingRegistryError:
            missing = True

        assert missing is True
        assert len(ianverfer.cues) == 3
        cue = ianverfer.cues.popleft()
        assert cue["kin"] == "saved"
        cue["creder"] = untargetedCreder.raw

        iss = ianiss.issue(said=untargetedCreder.said)
        rseal = SealEvent(iss.pre, "0", iss.said)._asdict()
        ian.interact(data=[rseal])
        seqner = coring.Seqner(sn=ian.kever.sn)
        ianiss.anchorMsg(pre=iss.pre,
                         regd=iss.said,
                         seqner=seqner,
                         saider=coring.Saider(qb64=ian.kever.serder.said))
        ianreg.processEscrows()

        # Now that the credential has been issued, process escrows and it will find the TEL event
        ianverfer.processEscrows()

        chainedSubject = dict(
            d="",
            dt=helping.nowIso8601(),
            claim="An outrageous claim.",
        )
        _, d = scheming.Saider.saidify(sad=chainedSubject, code=coring.MtrDex.Blake3_256, label=scheming.Saids.d)

        chainSad = dict(
            d='',
            untargetedButI2I=dict(
                n=untargetedCreder.said,
                o="I2I"
            ),
        )
        _, chain = scheming.Saider.saidify(sad=chainSad, code=coring.MtrDex.Blake3_256, label=scheming.Saids.d)

        chainedCreder = proving.credential(issuer=ian.pre,
                                           schema=optionalIssueeSchema,
                                           data=d,
                                           status=ianiss.regk,
                                           source=chain,
                                           rules={})

        missing = False
        try:
            ianverfer.processCredential(chainedCreder, prefixer=ian.kever.prefixer, seqner=seqner,
                                        saider=coring.Saider(qb64=ian.kever.serder.said))
        except kering.MissingRegistryError:
            missing = True

        assert missing is True
        assert len(ianverfer.cues) == 4
        cue = ianverfer.cues.popleft()
        assert cue["kin"] == "saved"
        cue["creder"] = chainedCreder.raw

        iss = ianiss.issue(said=chainedCreder.said)
        rseal = SealEvent(iss.pre, "0", iss.said)._asdict()
        ian.interact(data=[rseal])
        seqner = coring.Seqner(sn=ian.kever.sn)
        ianiss.anchorMsg(pre=iss.pre,
                         regd=iss.said,
                         seqner=seqner,
                         saider=coring.Saider(qb64=ian.kever.serder.said))
        ianreg.processEscrows()

        # Ensure that when specifying I2I it is enforced
        try:
            ianverfer.processCredential(chainedCreder, prefixer=ian.kever.prefixer, seqner=seqner,
                                        saider=coring.Saider(qb64=ian.kever.serder.said))
        except kering.MissingChainError:
            pass

        # Now lets get Ron's credential into Vic's Tevers and Database
        vickvy = ceventing.Kevery(db=vic.db, lax=False, local=False)
        victvy = eventing.Tevery(reger=vicreg.reger, db=vic.db, local=False)
        vicverfer = verifying.Verifier(hby=vicHby, reger=vicreg.reger)

        for msg in ron.db.clonePreIter(pre=ron.pre):
            parsing.Parser(version=Vrsn_1_0).parse(ims=bytearray(msg), kvy=vickvy, tvy=victvy)
        for msg in ronverfer.reger.clonePreIter(pre=roniss.regk):
            parsing.Parser(version=Vrsn_1_0).parse(ims=bytearray(msg), kvy=vickvy, tvy=victvy)
        for msg in ronverfer.reger.clonePreIter(pre=creder.said):
            parsing.Parser(version=Vrsn_1_0).parse(ims=bytearray(msg), kvy=vickvy, tvy=victvy)

        vicverfer.processCredential(creder, prefixer=ian.kever.prefixer, seqner=seqner,
                                    saider=coring.Saider(qb64=ian.kever.serder.said))
        assert len(vicverfer.cues) == 1
        cue = vicverfer.cues.popleft()
        assert cue["kin"] == "saved"
        assert cue["creder"].raw == creder.raw

        # Vic should be able to verify Han's credential
        # Get Ian's icp into Vic's db
        for msg in ian.db.clonePreIter(pre=ian.pre):
            parsing.Parser(version=Vrsn_1_0).parse(ims=bytearray(msg), kvy=vickvy, tvy=victvy)
        for msg in ianverfer.reger.clonePreIter(pre=ianiss.regk):
            parsing.Parser(version=Vrsn_1_0).parse(ims=bytearray(msg), kvy=vickvy, tvy=victvy)
        for msg in ianverfer.reger.clonePreIter(pre=vLeiCreder.said):
            parsing.Parser(version=Vrsn_1_0).parse(ims=bytearray(msg), kvy=vickvy, tvy=victvy)

        # And now verify the credential:
        vicverfer.processCredential(vLeiCreder, prefixer=ian.kever.prefixer, seqner=seqner,
                                    saider=coring.Saider(qb64=ian.kever.serder.said))

        assert len(vicverfer.cues) == 1
        cue = vicverfer.cues.popleft()
        assert cue["kin"] == "saved"
        assert cue["creder"].raw == vLeiCreder.raw

        # Revoke Ian's issuer credential and vic should no longer be able to verify
        # Han's credential that's linked to it
        rev = roniss.revoke(said=creder.said)
        rseq = coring.Seqner(sn=rev.sn)
        rseal = SealEvent(rev.pre, rseq.snh, rev.said)._asdict()
        ron.interact(data=[rseal])
        seqner = coring.Seqner(sn=ron.kever.sn)
        roniss.anchorMsg(pre=rev.pre,
                         regd=rev.said,
                         seqner=seqner,
                         saider=coring.Saider(qb64=ron.kever.serder.said))
        ronreg.processEscrows()

        for msg in ron.db.clonePreIter(pre=ron.pre):
            parsing.Parser(version=Vrsn_1_0).parse(ims=bytearray(msg), kvy=vickvy, tvy=victvy)
        for msg in ronverfer.reger.clonePreIter(pre=roniss.regk):
            parsing.Parser(version=Vrsn_1_0).parse(ims=bytearray(msg), kvy=vickvy, tvy=victvy)
        for msg in ronverfer.reger.clonePreIter(pre=creder.said):
            parsing.Parser(version=Vrsn_1_0).parse(ims=bytearray(msg), kvy=vickvy, tvy=victvy)

        with pytest.raises(kering.RevokedChainError):
            vicverfer.processCredential(vLeiCreder, prefixer=ian.kever.prefixer, seqner=seqner,
                                        saider=coring.Saider(qb64=ian.kever.serder.said))

        creds = ronreg.reger.cloneCreds(saids=[coring.Saider(qb64=creder.said)], db=ronHby.db)
        for cred in creds:
            assert cred['status']['et'] == 'rev'
            assert cred['rev'] is not None
            assert cred['rev']['i'] == creder.said
            assert cred['revatc'] is not None
            assert cred['revanc'] is not None
            assert cred['revanc']['s'] == '3'
            assert cred['revanc']['a'][0]['s'] == '1'
            assert cred['revancatc'] is not None

    """End Test"""
