from unittest import TestCase
from datetime import datetime, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo

from ..types import (
    BalanceCoordinate,
    CustomInstruction,
    DEFAULT_ADDRESS,
    DEFAULT_ASSET,
    EndOfMonthSchedule,
    AccountNotificationDirective,
    Phase,
    PlanNotificationDirective,
    Posting,
    PostingInstructionsDirective,
    PostingInstructionRejectionReason,
    Release,
    ScheduleExpression,
    ScheduleSkip,
    TransactionCode,
    Tside,
    UpdateAccountEventTypeDirective,
    UpdatePlanEventTypeDirective,
    
)
from .....utils.exceptions import (
    StrongTypingError,
    IllegalPython,
    InvalidSmartContractError,
)
from .....utils.types_utils import (
    ContractsLanguageDunderMixin,
)

from .....utils.feature_flags import (
    skip_if_not_enabled,
    EXPECTED_PID_REJECTIONS,
    disable_fflags,
    
)


class PublicCommonV400DirectivesTestCase(TestCase):
    def setUp(self) -> None:
        self.test_account_id = "test_test_account_id"
        self.test_naive_datetime = datetime(year=2021, month=1, day=1)
        self.test_zoned_datetime_utc = datetime(year=2021, month=1, day=1, tzinfo=ZoneInfo("UTC"))
        self.test_end_datetime = datetime(year=2021, month=2, day=1, tzinfo=ZoneInfo("UTC"))
        self.client_batch_id = "international-payment"
        pi_postings = [
            Posting(
                account_id=self.test_account_id,
                account_address=DEFAULT_ADDRESS,
                asset=DEFAULT_ASSET,
                credit=False,
                phase=Phase.COMMITTED,
                amount=Decimal(10),
                denomination="GBP",
            ),
            Posting(
                account_id="internal",
                account_address=DEFAULT_ADDRESS,
                asset=DEFAULT_ASSET,
                credit=True,
                phase=Phase.COMMITTED,
                amount=Decimal(10),
                denomination="GBP",
            ),
        ]
        transaction_code = TransactionCode(domain="A", family="B", subfamily="C")
        self.posting_instruction = CustomInstruction(
            postings=pi_postings,
            override_all_restrictions=True,
            transaction_code=transaction_code,
            instruction_details={"testy": "test"},
        )
        self.posting_instructions_directive = PostingInstructionsDirective(
            posting_instructions=[self.posting_instruction],
            client_batch_id=self.client_batch_id,
            value_datetime=self.test_naive_datetime.replace(tzinfo=ZoneInfo("UTC")),
            batch_details={"One Team": "One Meme"},
        )

    # PostingInstructionsDirective

    def test_posting_instructions_directive(self):
        posting_instructions = [self.posting_instruction]
        posting_instructions_directive = self.posting_instructions_directive
        self.assertEqual(self.client_batch_id, posting_instructions_directive.client_batch_id)
        self.assertEqual(
            self.test_naive_datetime.replace(tzinfo=ZoneInfo("UTC")),
            posting_instructions_directive.value_datetime,
        )
        self.assertEqual("One Meme", posting_instructions_directive.batch_details["One Team"])
        self.assertEqual(
            posting_instructions[0], posting_instructions_directive.posting_instructions[0]
        )
        # Both accounts postings are visible in the Postings list
        self.assertEqual(2, len(posting_instructions_directive.posting_instructions[0].postings))
        self.assertIn(
            posting_instructions_directive.posting_instructions[0].postings[0].account_id,
            [self.test_account_id, "internal"],
        )
        self.assertIn(
            posting_instructions_directive.posting_instructions[0].postings[1].account_id,
            [self.test_account_id, "internal"],
        )

        # Can get balances for in-flight CustomInstructions being directed

    def test_posting_instructions_directive_can_get_balances_for_inflight_custom_instructions(self):
        posting_instructions_directive = self.posting_instructions_directive
        balance_key_committed = BalanceCoordinate(
            account_address=DEFAULT_ADDRESS,
            asset=DEFAULT_ASSET,
            denomination="GBP",
            phase=Phase.COMMITTED,
        )
        self.assertEqual(
            Decimal(10),
            posting_instructions_directive.posting_instructions[0]
            .balances(account_id="internal", tside=Tside.LIABILITY)[balance_key_committed]
            .net,
        )
        self.assertEqual(
            Decimal(-10),
            posting_instructions_directive.posting_instructions[0]
            .balances(
                account_id=self.test_account_id,
                tside=Tside.LIABILITY,
            )[balance_key_committed]
            .net,
        )

    def test_posting_instructions_directive_repr_inherited_from_mixin(self):
        posting_instructions_directive = self.posting_instructions_directive
        self.assertTrue(issubclass(PostingInstructionsDirective, ContractsLanguageDunderMixin))
        self.assertIn("PostingInstructionsDirective", repr(posting_instructions_directive))

    def test_posting_instructions_directive_value_datetime_raises_with_naive_datetime(self):
        pi_postings = [
            Posting(
                account_id=self.test_account_id,
                account_address=DEFAULT_ADDRESS,
                asset=DEFAULT_ASSET,
                credit=False,
                phase=Phase.COMMITTED,
                amount=Decimal(10),
                denomination="GBP",
            ),
            Posting(
                account_id="internal",
                account_address=DEFAULT_ADDRESS,
                asset=DEFAULT_ASSET,
                credit=True,
                phase=Phase.COMMITTED,
                amount=Decimal(10),
                denomination="GBP",
            ),
        ]
        transaction_code = TransactionCode(domain="A", family="B", subfamily="C")
        pi = CustomInstruction(
            postings=pi_postings,
            override_all_restrictions=True,
            transaction_code=transaction_code,
            instruction_details={"testy": "test"},
        )
        with self.assertRaises(InvalidSmartContractError) as ex:
            PostingInstructionsDirective(
                posting_instructions=[pi],
                client_batch_id=self.client_batch_id,
                value_datetime=self.test_naive_datetime,
            )
        self.assertEqual(
            "'value_datetime' of PostingInstructionsDirective is not timezone aware.",
            str(ex.exception),
        )

    def test_posting_instructions_directive_value_datetime_raises_with_non_utc_timezone(self):
        pi_postings = [
            Posting(
                account_id=self.test_account_id,
                account_address=DEFAULT_ADDRESS,
                asset=DEFAULT_ASSET,
                credit=False,
                phase=Phase.COMMITTED,
                amount=Decimal(10),
                denomination="GBP",
            ),
            Posting(
                account_id="internal",
                account_address=DEFAULT_ADDRESS,
                asset=DEFAULT_ASSET,
                credit=True,
                phase=Phase.COMMITTED,
                amount=Decimal(10),
                denomination="GBP",
            ),
        ]
        transaction_code = TransactionCode(domain="A", family="B", subfamily="C")
        pi = CustomInstruction(
            postings=pi_postings,
            override_all_restrictions=True,
            transaction_code=transaction_code,
            instruction_details={"testy": "test"},
        )
        with self.assertRaises(InvalidSmartContractError) as ex:
            PostingInstructionsDirective(
                posting_instructions=[pi],
                client_batch_id=self.client_batch_id,
                value_datetime=self.test_naive_datetime.replace(tzinfo=ZoneInfo("US/Pacific")),
            )
        self.assertEqual(
            "'value_datetime' of PostingInstructionsDirective must have timezone UTC, currently US/Pacific.",
            str(ex.exception),
        )

    def test_posting_instructions_directive_value_datetime_raises_with_non_zoneinfo_timezone(self):
        pi_postings = [
            Posting(
                account_id=self.test_account_id,
                account_address=DEFAULT_ADDRESS,
                asset=DEFAULT_ASSET,
                credit=False,
                phase=Phase.COMMITTED,
                amount=Decimal(10),
                denomination="GBP",
            ),
            Posting(
                account_id="internal",
                account_address=DEFAULT_ADDRESS,
                asset=DEFAULT_ASSET,
                credit=True,
                phase=Phase.COMMITTED,
                amount=Decimal(10),
                denomination="GBP",
            ),
        ]
        transaction_code = TransactionCode(domain="A", family="B", subfamily="C")
        pi = CustomInstruction(
            postings=pi_postings,
            override_all_restrictions=True,
            transaction_code=transaction_code,
            instruction_details={"testy": "test"},
        )
        with self.assertRaises(InvalidSmartContractError) as ex:
            PostingInstructionsDirective(
                posting_instructions=[pi],
                client_batch_id=self.client_batch_id,
                value_datetime=datetime.fromtimestamp(1, timezone.utc),
            )
        self.assertEqual(
            "'value_datetime' of PostingInstructionsDirective must have timezone of type ZoneInfo, currently <class 'datetime.timezone'>.",
            str(ex.exception),
        )

    def test_posting_instructions_directive_defaults(self):
        pi1 = CustomInstruction(
            postings=[
                Posting(
                    account_id=self.test_account_id,
                    account_address=DEFAULT_ADDRESS,
                    asset=DEFAULT_ASSET,
                    credit=False,
                    phase=Phase.COMMITTED,
                    amount=Decimal(10),
                    denomination="GBP",
                ),
                Posting(
                    account_id="internal",
                    account_address=DEFAULT_ADDRESS,
                    asset=DEFAULT_ASSET,
                    credit=True,
                    phase=Phase.COMMITTED,
                    amount=Decimal(10),
                    denomination="GBP",
                ),
            ],
        )
        pi2 = CustomInstruction(
            postings=[
                Posting(
                    account_id="testty",
                    account_address="TEST",
                    asset=DEFAULT_ASSET,
                    credit=True,
                    phase=Phase.COMMITTED,
                    amount=Decimal(10),
                    denomination="GBP",
                ),
                Posting(
                    account_id="internal",
                    account_address="TEST",
                    asset=DEFAULT_ASSET,
                    credit=False,
                    phase=Phase.COMMITTED,
                    amount=Decimal(10),
                    denomination="GBP",
                ),
            ]
        )
        posting_instructions_directive = PostingInstructionsDirective(
            posting_instructions=[pi1, pi2],
        )
        self.assertIsNone(posting_instructions_directive.client_batch_id)
        self.assertIsNone(posting_instructions_directive.value_datetime)
        self.assertIsNone(posting_instructions_directive.booking_datetime)
        self.assertIsNone(posting_instructions_directive.batch_details)
        self.assertEqual(2, len(posting_instructions_directive.posting_instructions))
        # Both accounts postings are visible in the Postings list
        self.assertEqual(2, len(posting_instructions_directive.posting_instructions[0].postings))
        self.assertEqual(2, len(posting_instructions_directive.posting_instructions[1].postings))
        # Can get balances for in-flight CustomInstructions being directed
        balance_key_committed = BalanceCoordinate(
            account_address=DEFAULT_ADDRESS,
            asset=DEFAULT_ASSET,
            denomination="GBP",
            phase=Phase.COMMITTED,
        )
        self.assertEqual(
            Decimal(10),
            posting_instructions_directive.posting_instructions[0]
            .balances(account_id="internal", tside=Tside.LIABILITY)[balance_key_committed]
            .net,
        )
        self.assertEqual(
            Decimal(-10),
            posting_instructions_directive.posting_instructions[0]
            .balances(
                account_id=self.test_account_id,
                tside=Tside.LIABILITY,
            )[balance_key_committed]
            .net,
        )
        # Can get balances for in-flight CustomInstructions being directed
        self.assertEqual(
            Decimal(-10),
            posting_instructions_directive.posting_instructions[1]
            .balances(account_id="internal", tside=Tside.LIABILITY)[
                BalanceCoordinate(
                    account_address="TEST",
                    asset=DEFAULT_ASSET,
                    denomination="GBP",
                    phase=Phase.COMMITTED,
                )
            ]
            .net,
        )
        self.assertEqual(
            Decimal(0),
            posting_instructions_directive.posting_instructions[1]
            .balances(account_id=self.test_account_id, tside=Tside.LIABILITY)[
                BalanceCoordinate(
                    account_address="TEST",
                    asset=DEFAULT_ASSET,
                    denomination="GBP",
                    phase=Phase.COMMITTED,
                )
            ]
            .net,
        )
        self.assertEqual(
            Decimal(10),
            posting_instructions_directive.posting_instructions[1]
            .balances(account_id="testty", tside=Tside.LIABILITY)[
                BalanceCoordinate(
                    account_address="TEST",
                    asset=DEFAULT_ASSET,
                    denomination="GBP",
                    phase=Phase.COMMITTED,
                )
            ]
            .net,
        )

    def test_posting_instructions_directive_type_checking(self):
        posting_instructions_directive = PostingInstructionsDirective(
            posting_instructions=[Release(client_transaction_id="test")],
            _from_proto=True,
        )
        self.assertIsNone(posting_instructions_directive.client_batch_id)
        self.assertIsNone(posting_instructions_directive.value_datetime)
        self.assertIsNone(posting_instructions_directive.batch_details)
        self.assertIsNone(posting_instructions_directive.booking_datetime)
        self.assertEqual(1, len(posting_instructions_directive.posting_instructions))
        # Cannot get balances for in-flight Release
        with self.assertRaises(InvalidSmartContractError) as ex:
            posting_instructions_directive.posting_instructions[0].balances(
                account_id=self.test_account_id, tside=Tside.LIABILITY
            )
        self.assertEqual(
            "The Release posting instruction type does not support the balances method "
            "for the non-historical data as committed_postings are not available.",
            str(ex.exception),
        )

    def test_posting_instructions_directive_unsupported_type(self):
        with self.assertRaises(StrongTypingError) as ex:
            PostingInstructionsDirective(
                posting_instructions=[Release(client_transaction_id="test")],
            )
        expected = "Expected List[CustomInstruction], got 'Release"
        self.assertIn(expected, str(ex.exception))

    def test_posting_instructions_directive_raises_no_posting_instructions(self):
        with self.assertRaises(InvalidSmartContractError) as ex:
            PostingInstructionsDirective(
                posting_instructions=[],
            )
        self.assertIn(
            "'posting_instructions' must be a non empty list, got []",
            str(ex.exception),
        )

    def test_posting_instructions_directive_skips_with_from_proto(self):
        directive = PostingInstructionsDirective(posting_instructions=[], _from_proto=True)
        self.assertEqual([], directive.posting_instructions)

    def test_posting_instructions_directive_raises_when_net_non_zero(self):
        with self.assertRaises(InvalidSmartContractError) as ex:
            PostingInstructionsDirective(
                posting_instructions=[
                    CustomInstruction(
                        postings=[
                            Posting(
                                account_address="DEFAULT",
                                account_id=self.test_account_id,
                                amount=Decimal(40),
                                denomination="GBP",
                                phase=Phase.PENDING_OUT,
                                asset=DEFAULT_ASSET,
                                credit=True,
                            ),
                            Posting(
                                account_address="DEFAULT",
                                account_id="1",
                                amount=Decimal(37),
                                denomination="GBP",
                                phase=Phase.PENDING_OUT,
                                asset=DEFAULT_ASSET,
                                credit=False,
                            ),
                        ]
                    ),
                ],
            )
        self.assertEqual(
            "Net of balance coordinate ('COMMERCIAL_BANK_MONEY', 'GBP', Phase.PENDING_OUT)"
            " in the CustomInstruction: 3, Expected: 0.",
            str(ex.exception),
        )

    def test_posting_instructions_directive_happy_path_when_net_zero(self):
        posting_instructions_directive = PostingInstructionsDirective(
            posting_instructions=[
                CustomInstruction(
                    postings=[
                        Posting(
                            account_address="DEFAULT",
                            account_id=self.test_account_id,
                            amount=Decimal(10),
                            denomination="STONKS",
                            phase=Phase.COMMITTED,
                            asset="SOMA",
                            credit=True,
                        ),
                        Posting(
                            account_address="RETIREMENT_POT",
                            account_id="1",
                            amount=Decimal(10),
                            denomination="STONKS",
                            phase=Phase.COMMITTED,
                            asset="SOMA",
                            credit=False,
                        ),
                    ]
                ),
            ],
        )

        self.assertIsNone(posting_instructions_directive.client_batch_id)
        self.assertIsNone(posting_instructions_directive.value_datetime)
        self.assertIsNone(posting_instructions_directive.booking_datetime)
        self.assertIsNone(posting_instructions_directive.batch_details)
        self.assertEqual(1, len(posting_instructions_directive.posting_instructions))
        self.assertEqual(2, len(posting_instructions_directive.posting_instructions[0].postings))
        self.assertEqual(
            Decimal(10),
            posting_instructions_directive.posting_instructions[0]
            .balances(account_id=self.test_account_id, tside=Tside.LIABILITY)[
                BalanceCoordinate(
                    account_address="DEFAULT",
                    asset="SOMA",
                    denomination="STONKS",
                    phase=Phase.COMMITTED,
                )
            ]
            .net,
        )
        self.assertEqual(
            Decimal(-10),
            posting_instructions_directive.posting_instructions[0]
            .balances(account_id="1", tside=Tside.LIABILITY)[
                BalanceCoordinate(
                    account_address="RETIREMENT_POT",
                    asset="SOMA",
                    denomination="STONKS",
                    phase=Phase.COMMITTED,
                )
            ]
            .net,
        )

    def test_posting_instructions_directive_validates_net_zero_sum_across_multiple_accounts_ids(
        self,
    ):
        # Test the zero net sum validation when the Postings of a CustomInstruction affect multiple
        # account ids.
        posting_instructions_directive = PostingInstructionsDirective(
            posting_instructions=[
                CustomInstruction(
                    postings=[
                        Posting(
                            account_address="DEFAULT",
                            account_id="1",  # Internal Account
                            amount=Decimal(1000),
                            denomination="GBP",
                            phase=Phase.COMMITTED,
                            asset=DEFAULT_ASSET,
                            credit=True,
                        ),
                        # The amount for the same BalanceCoordinate is debited from multiple
                        # accounts.
                        Posting(
                            account_address="DEFAULT",
                            account_id="account_id_1",
                            amount=Decimal(700),
                            denomination="GBP",
                            phase=Phase.COMMITTED,
                            asset=DEFAULT_ASSET,
                            credit=False,
                        ),
                        Posting(
                            account_address="DEFAULT",
                            account_id="account_id_2",
                            amount=Decimal(300),
                            denomination="GBP",
                            phase=Phase.COMMITTED,
                            asset=DEFAULT_ASSET,
                            credit=False,
                        ),
                    ]
                ),
            ],
        )

        self.assertIsNone(posting_instructions_directive.client_batch_id)
        self.assertIsNone(posting_instructions_directive.value_datetime)
        self.assertIsNone(posting_instructions_directive.booking_datetime)
        self.assertIsNone(posting_instructions_directive.batch_details)
        self.assertEqual(1, len(posting_instructions_directive.posting_instructions))
        self.assertEqual(3, len(posting_instructions_directive.posting_instructions[0].postings))

    def test_posting_instructions_directive_raises_if_limit_of_posting_instructions_breached(self):
        with self.assertRaises(InvalidSmartContractError) as ex:
            PostingInstructionsDirective(
                posting_instructions=[
                    CustomInstruction(
                        postings=[
                            Posting(
                                amount=Decimal(1),
                                credit=True,
                                account_id="1",
                                denomination="GBP",
                                account_address=DEFAULT_ADDRESS,
                                asset=DEFAULT_ASSET,
                                phase=Phase.COMMITTED,
                            ),
                        ],
                    ),
                ]
                * 65,
            )
        self.assertIn(
            "Too many posting instructions submitted in the Posting Instructions Directive. "
            "Number submitted: 65. Limit: 64.",
            str(ex.exception),
        )

    def test_posting_instructions_directive_raises_if_limit_of_postings_in_custom_instruction_breached(
        self,
    ):
        with self.assertRaises(InvalidSmartContractError) as ex:
            PostingInstructionsDirective(
                posting_instructions=[
                    CustomInstruction(
                        postings=[
                            Posting(
                                amount=Decimal(1),
                                credit=True,
                                account_id="1",
                                denomination="GBP",
                                account_address=DEFAULT_ADDRESS,
                                asset=DEFAULT_ASSET,
                                phase=Phase.COMMITTED,
                            ),
                        ]
                        * 65,
                    ),
                ],
            )
        self.assertIn(
            "Too many postings submitted in the CustomInstruction. "
            "Number submitted: 65. Limit: 64.",
            str(ex.exception),
        )

    def test_posting_instructions_directive_batch_details_raises_with_incorrect_type(self):
        pi_postings = [
            Posting(
                account_id=self.test_account_id,
                account_address=DEFAULT_ADDRESS,
                asset=DEFAULT_ASSET,
                credit=False,
                phase=Phase.COMMITTED,
                amount=Decimal(10),
                denomination="GBP",
            ),
            Posting(
                account_id="internal",
                account_address=DEFAULT_ADDRESS,
                asset=DEFAULT_ASSET,
                credit=True,
                phase=Phase.COMMITTED,
                amount=Decimal(10),
                denomination="GBP",
            ),
        ]
        pi = CustomInstruction(postings=pi_postings)
        with self.assertRaises(StrongTypingError) as ex:
            PostingInstructionsDirective(
                posting_instructions=[pi],
                batch_details="One Team, One Meme",
            )
        self.assertEqual(
            "'PostingInstructionsDirective.batch_details' expected Dict[str, str] if "
            "populated, got 'One Team, One Meme' of type str",
            str(ex.exception),
        )

    def test_posting_instructions_directive_with_booking_datetime(self):
        pi_postings = [
            Posting(
                account_id=self.test_account_id,
                account_address=DEFAULT_ADDRESS,
                asset=DEFAULT_ASSET,
                credit=False,
                phase=Phase.COMMITTED,
                amount=Decimal(10),
                denomination="GBP",
            ),
            Posting(
                account_id="internal",
                account_address=DEFAULT_ADDRESS,
                asset=DEFAULT_ASSET,
                credit=True,
                phase=Phase.COMMITTED,
                amount=Decimal(10),
                denomination="GBP",
            ),
        ]
        transaction_code = TransactionCode(domain="A", family="B", subfamily="C")
        pi = CustomInstruction(
            postings=pi_postings,
            override_all_restrictions=True,
            transaction_code=transaction_code,
            instruction_details={"testy": "test"},
        )
        booking_datetime = datetime(year=2020, month=12, day=31, tzinfo=ZoneInfo("UTC"))
        posting_instructions_directive = PostingInstructionsDirective(
            posting_instructions=[pi],
            client_batch_id=self.client_batch_id,
            booking_datetime=booking_datetime,
            value_datetime=self.test_naive_datetime.replace(tzinfo=ZoneInfo("UTC")),
            batch_details={"One Team": "One Meme"},
        )
        self.assertEqual(self.client_batch_id, posting_instructions_directive.client_batch_id)
        self.assertEqual(
            self.test_naive_datetime.replace(tzinfo=ZoneInfo("UTC")),
            posting_instructions_directive.value_datetime,
        )
        self.assertEqual(booking_datetime, posting_instructions_directive.booking_datetime)
        self.assertEqual("One Meme", posting_instructions_directive.batch_details["One Team"])
        self.assertEqual(pi, posting_instructions_directive.posting_instructions[0])
        # Both accounts postings are visible in the Postings list
        self.assertEqual(2, len(posting_instructions_directive.posting_instructions[0].postings))
        self.assertIn(
            posting_instructions_directive.posting_instructions[0].postings[0].account_id,
            [self.test_account_id, "internal"],
        )
        self.assertIn(
            posting_instructions_directive.posting_instructions[0].postings[1].account_id,
            [self.test_account_id, "internal"],
        )

        # Can get balances for in-flight CustomInstructions being directed
        balance_key_committed = BalanceCoordinate(
            account_address=DEFAULT_ADDRESS,
            asset=DEFAULT_ASSET,
            denomination="GBP",
            phase=Phase.COMMITTED,
        )
        self.assertEqual(
            Decimal(10),
            posting_instructions_directive.posting_instructions[0]
            .balances(account_id="internal", tside=Tside.LIABILITY)[balance_key_committed]
            .net,
        )
        self.assertEqual(
            Decimal(-10),
            posting_instructions_directive.posting_instructions[0]
            .balances(
                account_id=self.test_account_id,
                tside=Tside.LIABILITY,
            )[balance_key_committed]
            .net,
        )

    def test_posting_instructions_directive_raises_with_invalid_booking_datetime(self):
        pi_postings = [
            Posting(
                account_id=self.test_account_id,
                account_address=DEFAULT_ADDRESS,
                asset=DEFAULT_ASSET,
                credit=False,
                phase=Phase.COMMITTED,
                amount=Decimal(10),
                denomination="GBP",
            ),
            Posting(
                account_id="internal",
                account_address=DEFAULT_ADDRESS,
                asset=DEFAULT_ASSET,
                credit=True,
                phase=Phase.COMMITTED,
                amount=Decimal(10),
                denomination="GBP",
            ),
        ]
        transaction_code = TransactionCode(domain="A", family="B", subfamily="C")
        pi = CustomInstruction(
            postings=pi_postings,
            override_all_restrictions=True,
            transaction_code=transaction_code,
            instruction_details={"testy": "test"},
        )
        booking_datetime = "1st April 2023"
        with self.assertRaises(StrongTypingError) as ex:
            PostingInstructionsDirective(
                posting_instructions=[pi],
                client_batch_id=self.client_batch_id,
                booking_datetime=booking_datetime,
                value_datetime=self.test_naive_datetime.replace(tzinfo=ZoneInfo("UTC")),
                batch_details={"One Team": "One Meme"},
            )
        expected = "Expected datetime, got '1st April 2023' of type str"
        self.assertEqual(expected, str(ex.exception))

    def test_posting_instructions_directive_raises_when_both_account_id_and_processing_label_provided(
        self,
    ):
        with self.assertRaises(InvalidSmartContractError) as ex:
            PostingInstructionsDirective(
                posting_instructions=[
                    CustomInstruction(
                        postings=[
                            Posting(
                                account_address="DEFAULT",
                                account_id=self.test_account_id,
                                internal_account_processing_label="test_processing_label",
                                amount=Decimal(40),
                                denomination="GBP",
                                phase=Phase.PENDING_OUT,
                                asset=DEFAULT_ASSET,
                                credit=True,
                            ),
                            Posting(
                                account_address="DEFAULT",
                                account_id="1",
                                amount=Decimal(40),
                                denomination="GBP",
                                phase=Phase.PENDING_OUT,
                                asset=DEFAULT_ASSET,
                                credit=False,
                            ),
                        ]
                    ),
                ],
            )
        self.assertEqual(
            "Either account_id or internal_account_processing_label must be provided, not both. "
            "Got account_id 'test_test_account_id' and internal_account_processing_label 'test_processing_label'",
            str(ex.exception),
        )

    @skip_if_not_enabled(EXPECTED_PID_REJECTIONS)
    def test_posting_instructions_directive_with_non_blocking_rejection_reasons(self):
        non_blocking_rejection_reasons = set(
            [
                PostingInstructionRejectionReason.INSUFFICIENT_FUNDS,
                PostingInstructionRejectionReason.ACCOUNT_STATUS_INVALID,
            ]
        )
        posting_instructions_directive = PostingInstructionsDirective(
            posting_instructions=[self.posting_instruction],
            client_batch_id=self.client_batch_id,
            value_datetime=self.test_zoned_datetime_utc,
            non_blocking_rejection_reasons=non_blocking_rejection_reasons,
        )
        self.assertEqual(
            [self.posting_instruction], posting_instructions_directive.posting_instructions
        )
        self.assertEqual(self.client_batch_id, posting_instructions_directive.client_batch_id)
        self.assertEqual(
            self.test_zoned_datetime_utc, posting_instructions_directive.value_datetime
        )
        self.assertEqual(
            non_blocking_rejection_reasons,
            posting_instructions_directive.non_blocking_rejection_reasons,
        )

    @skip_if_not_enabled(EXPECTED_PID_REJECTIONS)
    def test_posting_instructions_directive_rejection_reasons_defaults(self):
        posting_instructions_directive = PostingInstructionsDirective(
            posting_instructions=[self.posting_instruction],
            client_batch_id=self.client_batch_id,
            value_datetime=self.test_zoned_datetime_utc,
            # non_blocking_rejection_reasons not provided.
        )
        # non_blocking_rejection_reasons defaults to an empty set.
        self.assertEqual(posting_instructions_directive.non_blocking_rejection_reasons, set())

    @skip_if_not_enabled(EXPECTED_PID_REJECTIONS)
    def test_posting_instructions_directive_empty_rejection_reasons(self):
        posting_instructions_directive = PostingInstructionsDirective(
            posting_instructions=[self.posting_instruction],
            client_batch_id=self.client_batch_id,
            value_datetime=self.test_zoned_datetime_utc,
            non_blocking_rejection_reasons=set(),
        )
        # non_blocking_rejection_reasons defaults to an empty set.
        self.assertEqual(posting_instructions_directive.non_blocking_rejection_reasons, set())

    @skip_if_not_enabled(EXPECTED_PID_REJECTIONS)
    def test_posting_instructions_directive_raises_with_invalid_rejection_reasons_type(
        self,
    ):
        with self.assertRaises(StrongTypingError) as ex:
            PostingInstructionsDirective(
                posting_instructions=[self.posting_instruction],
                client_batch_id=self.client_batch_id,
                value_datetime=self.test_zoned_datetime_utc,
                booking_datetime=self.test_zoned_datetime_utc,
                non_blocking_rejection_reasons=2,  # Invalid value type.
            )
        self.assertIn(
            "Expected Set[PostingInstructionRejectionReason] for "
            "'PostingInstructionsDirective.non_blocking_rejection_reasons', got '2' of type int",
            str(ex.exception),
        )

    @skip_if_not_enabled(EXPECTED_PID_REJECTIONS)
    def test_posting_instructions_directive_raises_with_invalid_rejection_reasons_collection_type(
        self,
    ):
        with self.assertRaises(StrongTypingError) as ex:
            PostingInstructionsDirective(
                posting_instructions=[self.posting_instruction],
                client_batch_id=self.client_batch_id,
                value_datetime=self.test_zoned_datetime_utc,
                non_blocking_rejection_reasons=[
                    PostingInstructionRejectionReason.ACCOUNT_STATUS_INVALID
                ],  # list instead of set
            )
        self.assertIn(
            "Expected Set[PostingInstructionRejectionReason] for "
            "'PostingInstructionsDirective.non_blocking_rejection_reasons', got '[PostingInstructionRejectionReason.ACCOUNT_STATUS_INVALID]' of type list",
            str(ex.exception),
        )

    @skip_if_not_enabled(EXPECTED_PID_REJECTIONS)
    def test_posting_instructions_directive_raises_with_invalid_rejection_reasons_element_type(
        self,
    ):
        with self.assertRaises(StrongTypingError) as ex:
            PostingInstructionsDirective(
                posting_instructions=[self.posting_instruction],
                client_batch_id=self.client_batch_id,
                value_datetime=self.test_zoned_datetime_utc,
                non_blocking_rejection_reasons={2},  # Invalid list element type.
            )
        self.assertIn(
            "'PostingInstructionsDirective.non_blocking_rejection_reasons[0]' "
            "expected PostingInstructionRejectionReason, got '2' of type int",
            str(ex.exception),
        )

    @skip_if_not_enabled(EXPECTED_PID_REJECTIONS)
    def test_posting_instructions_directive_rejection_reasons_validation_skipped_with_from_proto(
        self,
    ):
        posting_instructions_directive = PostingInstructionsDirective(
            posting_instructions=[self.posting_instruction],
            client_batch_id=self.client_batch_id,
            value_datetime=self.test_naive_datetime.replace(tzinfo=ZoneInfo("UTC")),
            non_blocking_rejection_reasons=2,  # Invalid type for class attribute.
            _from_proto=True,  # Skips validation.
        )
        self.assertEqual(2, posting_instructions_directive.non_blocking_rejection_reasons)

    @disable_fflags([EXPECTED_PID_REJECTIONS])
    def test_posting_instructions_directive_with_non_blocking_rejection_reasons_raises_if_fflag_disabled(
        self,
    ):
        non_blocking_rejection_reasons = [
            PostingInstructionRejectionReason.INSUFFICIENT_FUNDS,
            PostingInstructionRejectionReason.ACCOUNT_STATUS_INVALID,
        ]
        with self.assertRaises(IllegalPython) as ex:
            PostingInstructionsDirective(
                posting_instructions=[self.posting_instruction],
                client_batch_id=self.client_batch_id,
                value_datetime=self.test_zoned_datetime_utc,
                non_blocking_rejection_reasons=non_blocking_rejection_reasons,
            )
        self.assertEqual(
            "PostingInstructionsDirective.__init__() got unexpected keyword argument "
            "'non_blocking_rejection_reasons'",
            str(ex.exception),
        )

    # AccountNotificationDirective

    def test_account_notification_directive_raises_with_missing_details(self):
        notification_type = "test_notification_type"
        notification_details = {}
        with self.assertRaises(InvalidSmartContractError) as ex:
            AccountNotificationDirective(
                notification_type=notification_type,
                notification_details=notification_details,
            )
        expected = "AccountNotificationDirective 'notification_details' must be populated"
        self.assertEqual(expected, str(ex.exception))

    def test_account_notification_directive_equality(self):
        notification_type = "test_notification_type"
        notification_details = {"key": "value"}

        account_notification_directive = AccountNotificationDirective(
            notification_type=notification_type,
            notification_details=notification_details,
        )

        other_account_notification_directive = AccountNotificationDirective(
            notification_type=notification_type,
            notification_details=notification_details,
        )

        self.assertEqual(account_notification_directive, other_account_notification_directive)

    def test_account_notification_directive_unequal_notification_details(self):
        notification_type = "test_notification_type"
        notification_details = {"key": "value"}
        other_notification_details = {"key": "value2"}

        account_notification_directive = AccountNotificationDirective(
            notification_type=notification_type,
            notification_details=notification_details,
        )

        other_account_notification_directive = AccountNotificationDirective(
            notification_type=notification_type,
            notification_details=other_notification_details,
        )

        self.assertNotEqual(account_notification_directive, other_account_notification_directive)

    def test_account_notification_repr(self):
        obj = AccountNotificationDirective(
            notification_type="test_notification_type",
            notification_details={"key": "value"},
        )
        expected = (
            "AccountNotificationDirective(notification_type='test_notification_type', "
            + "notification_details={'key': 'value'})"
        )
        self.assertEqual(expected, repr(obj))

    # UpdateAccountEventTypeDirective

    def test_update_account_event_type_directive_can_be_created(self):
        update_account_event_type_directive = UpdateAccountEventTypeDirective(
            event_type="event_type_1",
            end_datetime=self.test_zoned_datetime_utc,
        )
        self.assertEqual(update_account_event_type_directive.event_type, "event_type_1")
        self.assertEqual(
            update_account_event_type_directive.end_datetime, self.test_zoned_datetime_utc
        )

    def test_update_account_event_type_directive_repr(self):
        directive = UpdateAccountEventTypeDirective(
            event_type="event_type_1", end_datetime=self.test_zoned_datetime_utc
        )
        expected = (
            "UpdateAccountEventTypeDirective(event_type='event_type_1', "
            + "expression=None, schedule_method=None, "
            + "end_datetime=datetime.datetime(2021, 1, 1, 0, 0, "
            + "tzinfo=zoneinfo.ZoneInfo(key='UTC')), skip=None)"
        )
        self.maxDiff = None
        self.assertEqual(expected, repr(directive))

    def test_update_account_event_type_directive_equality(self):
        schedule_method = EndOfMonthSchedule(day=1)
        update_account_event_type_directive = UpdateAccountEventTypeDirective(
            event_type="event_type_1",
            schedule_method=schedule_method,
        )
        other_schedule_method = EndOfMonthSchedule(day=1)
        other_update_account_event_type_directive = UpdateAccountEventTypeDirective(
            event_type="event_type_1",
            schedule_method=other_schedule_method,
        )
        self.assertEqual(
            update_account_event_type_directive, other_update_account_event_type_directive
        )

    def test_update_account_event_type_directive_unequal_schedule_method(self):
        schedule_method = EndOfMonthSchedule(day=1)
        update_account_event_type_directive = UpdateAccountEventTypeDirective(
            event_type="event_type_1",
            schedule_method=schedule_method,
        )
        other_schedule_method = EndOfMonthSchedule(day=2)
        other_update_account_event_type_directive = UpdateAccountEventTypeDirective(
            event_type="event_type_2",
            schedule_method=other_schedule_method,
        )
        self.assertNotEqual(
            update_account_event_type_directive, other_update_account_event_type_directive
        )

    def test_update_account_event_type_directive_raises_with_naive_end_datetime(self):
        with self.assertRaises(InvalidSmartContractError) as ex:
            UpdateAccountEventTypeDirective(
                event_type="event_type_1",
                end_datetime=self.test_naive_datetime,
            )
        self.assertIn(
            "'end_datetime' of UpdateAccountEventTypeDirective is not timezone aware.",
            str(ex.exception),
        )

    def test_update_account_event_type_directive_raises_with_naive_skip_end_datetime(self):
        with self.assertRaises(InvalidSmartContractError) as ex:
            UpdateAccountEventTypeDirective(
                event_type="event_type_1",
                skip=ScheduleSkip(end=self.test_naive_datetime),
            )
        self.assertEqual(
            "'end' of ScheduleSkip is not timezone aware.",
            str(ex.exception),
        )

    def test_update_account_event_type_directive_no_end_datetime_or_schedule(self):
        with self.assertRaises(InvalidSmartContractError) as ex:
            UpdateAccountEventTypeDirective(
                event_type="event_type_1",
            )

        self.assertIn(
            "UpdateAccountEventTypeDirective object must "
            "have either an end_datetime, an expression",
            str(ex.exception),
        )

    def test_update_account_event_type_directive_with_schedule_method(self):
        schedule_method = EndOfMonthSchedule(day=1)
        update_account_event_type_directive = UpdateAccountEventTypeDirective(
            event_type="event_type_1",
            schedule_method=schedule_method,
        )
        self.assertEqual(update_account_event_type_directive.event_type, "event_type_1")
        self.assertEqual(update_account_event_type_directive.schedule_method, schedule_method)

    def test_update_account_event_type_directive_validation(self):
        with self.assertRaises(InvalidSmartContractError) as ex:
            UpdateAccountEventTypeDirective(
                event_type="event_type_1",
                schedule_method=EndOfMonthSchedule(day=1),
                expression=ScheduleExpression(day="1"),
            )
        self.assertEqual(
            "UpdateAccountEventTypeDirective cannot contain both"
            " expression and schedule_method fields",
            str(ex.exception),
        )

    def test_update_account_event_type_directive_invalid_end_datetime(self):
        with self.assertRaises(StrongTypingError) as ex:
            UpdateAccountEventTypeDirective(
                event_type="event_type_1",
                end_datetime=False,
            )
        self.assertEqual("Expected datetime, got 'False' of type bool", str(ex.exception))

    def test_update_account_event_type_directive_skip_indefinitely(self):
        update_account_event_type_directive = UpdateAccountEventTypeDirective(
            event_type="event_type_1",
            skip=True,
        )
        self.assertTrue(update_account_event_type_directive.skip)

    def test_update_account_event_type_directive_skip_some_time(self):
        update_account_event_type_directive = UpdateAccountEventTypeDirective(
            event_type="event_type_1",
            skip=ScheduleSkip(
                end=datetime(year=2021, month=6, day=28, tzinfo=ZoneInfo("US/Pacific"))
            ),
        )
        self.assertEqual(
            datetime(year=2021, month=6, day=28, tzinfo=ZoneInfo("US/Pacific")),
            update_account_event_type_directive.skip.end,
        )

    def test_update_account_event_type_directive_unskip(self):
        update_account_event_type_directive = UpdateAccountEventTypeDirective(
            event_type="event_type_1",
            skip=False,
        )
        self.assertFalse(update_account_event_type_directive.skip)

    def test_update_account_event_type_directive_skip_invalid_end(self):
        with self.assertRaises(StrongTypingError) as ex:
            UpdateAccountEventTypeDirective(
                event_type="event_type_1",
                skip=ScheduleSkip(end=False),
            )
        self.assertEqual("Expected datetime, got 'False' of type bool", str(ex.exception))

    # UpdatePlanEventTypeDirective

    def test_update_plan_event_type_directive_validation(self):
        with self.assertRaises(InvalidSmartContractError) as ex:
            UpdatePlanEventTypeDirective(
                event_type="event_type_1",
                schedule_method=EndOfMonthSchedule(day=1),
                expression=ScheduleExpression(day="1"),
            )
        self.assertEqual(
            "UpdatePlanEventTypeDirective cannot contain both"
            " expression and schedule_method fields",
            str(ex.exception),
        )

    def test_update_plan_event_type_directive_invalid_constructor_arg_type(self):
        with self.assertRaises(StrongTypingError) as ex:
            UpdatePlanEventTypeDirective(
                event_type="event_type",
                expression=1,  # EventTypeSchedule expected.
            )
        self.assertEqual("Expected ScheduleExpression, got '1' of type int", str(ex.exception))

    def test_update_plan_event_type_directive_raises_with_naive_skip_end_datetime(self):
        with self.assertRaises(InvalidSmartContractError) as ex:
            UpdatePlanEventTypeDirective(
                event_type="event_type_1",
                skip=ScheduleSkip(end=self.test_naive_datetime),
            )
        self.assertEqual(
            "'end' of ScheduleSkip is not timezone aware.",
            str(ex.exception),
        )

    def test_update_plan_event_type_directive_raises_with_naive_end_datetime(self):
        with self.assertRaises(InvalidSmartContractError) as ex:
            UpdatePlanEventTypeDirective(
                event_type="event_type_1",
                end_datetime=self.test_naive_datetime,
            )
        self.assertIn(
            "'end_datetime' of UpdatePlanEventTypeDirective is not timezone aware.",
            str(ex.exception),
        )

    def test_update_plan_event_type_directive(self):
        schedule_method = EndOfMonthSchedule(day=1)
        update_plan_event_type_directive = UpdatePlanEventTypeDirective(
            event_type="event_type_1",
            end_datetime=self.test_end_datetime,
            schedule_method=schedule_method,
            skip=True,
        )
        self.assertEqual("event_type_1", update_plan_event_type_directive.event_type)
        self.assertEqual(self.test_end_datetime, update_plan_event_type_directive.end_datetime)
        self.assertEqual(update_plan_event_type_directive.schedule_method, schedule_method)
        self.assertTrue(update_plan_event_type_directive.skip)

    def test_update_plan_event_type_directive_repr(self):
        schedule_method = EndOfMonthSchedule(day=1)
        update_plan_event_type_directive = UpdatePlanEventTypeDirective(
            event_type="event_type_1",
            end_datetime=self.test_end_datetime,
            schedule_method=schedule_method,
            skip=True,
        )
        expected = (
            "UpdatePlanEventTypeDirective(event_type='event_type_1', "
            + "expression=None, schedule_method=EndOfMonthSchedule(day=1, hour=0, "
            + "minute=0, second=0, failover=ScheduleFailover.FIRST_VALID_DAY_BEFORE), "
            + "end_datetime=datetime.datetime(2021, 2, 1, 0, 0, "
            + "tzinfo=zoneinfo.ZoneInfo(key='UTC')), skip=True)"
        )
        self.maxDiff = None
        self.assertEqual(expected, repr(update_plan_event_type_directive))

    def test_update_plan_event_type_directive_equality(self):
        schedule_method = EndOfMonthSchedule(day=1)
        update_plan_event_type_directive = UpdatePlanEventTypeDirective(
            event_type="event_type_1",
            end_datetime=self.test_end_datetime,
            schedule_method=schedule_method,
            skip=True,
        )
        other_schedule_method = EndOfMonthSchedule(day=1)
        other_update_plan_event_type_directive = UpdatePlanEventTypeDirective(
            event_type="event_type_1",
            end_datetime=self.test_end_datetime,
            schedule_method=other_schedule_method,
            skip=True,
        )
        self.assertEqual(update_plan_event_type_directive, other_update_plan_event_type_directive)

    def test_update_plan_event_type_directive_unequal_schedule_method(self):
        schedule_method = EndOfMonthSchedule(day=1)
        update_plan_event_type_directive = UpdatePlanEventTypeDirective(
            event_type="event_type_1",
            end_datetime=self.test_end_datetime,
            schedule_method=schedule_method,
            skip=True,
        )
        other_schedule_method = EndOfMonthSchedule(day=2)
        other_update_plan_event_type_directive = UpdatePlanEventTypeDirective(
            event_type="event_type_1",
            end_datetime=self.test_end_datetime,
            schedule_method=other_schedule_method,
            skip=True,
        )
        self.assertNotEqual(
            update_plan_event_type_directive, other_update_plan_event_type_directive
        )

    def test_update_plan_event_type_directive_skip_false(self):
        update_plan_event_type_directive = UpdatePlanEventTypeDirective(
            event_type="event_type_1",
            end_datetime=self.test_end_datetime,
            skip=False,
        )
        self.assertEqual("event_type_1", update_plan_event_type_directive.event_type)
        self.assertEqual(self.test_end_datetime, update_plan_event_type_directive.end_datetime)
        self.assertFalse(update_plan_event_type_directive.skip)

    def test_update_plan_event_type_directive_schedule_skip(self):
        skip_end = datetime(year=2021, month=1, day=1, tzinfo=ZoneInfo("UTC"))
        update_plan_event_type_directive = UpdatePlanEventTypeDirective(
            event_type="event_type_1",
            end_datetime=self.test_end_datetime,
            skip=ScheduleSkip(end=skip_end),
        )
        self.assertEqual("event_type_1", update_plan_event_type_directive.event_type)
        self.assertEqual(self.test_end_datetime, update_plan_event_type_directive.end_datetime)
        self.assertIsNotNone(update_plan_event_type_directive.skip)
        self.assertEqual(skip_end, update_plan_event_type_directive.skip.end)

    def test_update_plan_event_type_directive_raises_with_no_end_datetime_or_schedule(self):
        with self.assertRaises(InvalidSmartContractError) as ex:
            UpdatePlanEventTypeDirective(
                event_type="event_type_1",
            )

        self.assertIn(
            ("UpdatePlanEventTypeDirective object has to have either an end_datetime, an "),
            str(ex.exception),
        )

    def test_update_plan_event_type_directive_raises_with_invalid_skip_attribute(self):
        with self.assertRaises(StrongTypingError) as ex:
            UpdatePlanEventTypeDirective(
                event_type="event_type_1",
                end_datetime=self.test_end_datetime,
                skip="not_valid",
            )
        self.assertEqual(
            "'skip' expected Optional[Union[bool, ScheduleSkip]], got 'not_valid' of type str",
            str(ex.exception),
        )

    # PlanNotificationDirective

    def test_plan_notification_directive(self):
        notification_type = "test_notification_type"
        notification_details = {"key1": "value1"}
        plan_notification_directive = PlanNotificationDirective(
            notification_type=notification_type,
            notification_details=notification_details,
        )
        self.assertEqual(notification_type, plan_notification_directive.notification_type)
        self.assertEqual(notification_details, plan_notification_directive.notification_details)

    def test_plan_notification_directive_repr(self):
        notification_type = "test_notification_type"
        notification_details = {"key1": "value1"}
        plan_notification_directive = PlanNotificationDirective(
            notification_type=notification_type,
            notification_details=notification_details,
        )
        expected = (
            "PlanNotificationDirective(notification_type='test_notification_type', "
            + "notification_details={'key1': 'value1'})"
        )
        self.assertEqual(expected, repr(plan_notification_directive))

    def test_plan_notification_directive_missing_details_raises(self):
        notification_type = "test_notification_type"
        notification_details = {}
        with self.assertRaises(InvalidSmartContractError) as ex:
            PlanNotificationDirective(
                notification_type=notification_type,
                notification_details=notification_details,
            )
        expected = "PlanNotificationDirective 'notification_details' must be populated"
        self.assertEqual(expected, str(ex.exception))

    
