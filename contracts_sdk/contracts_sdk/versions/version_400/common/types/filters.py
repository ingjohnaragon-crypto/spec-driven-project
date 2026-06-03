from functools import lru_cache


from .....utils import exceptions, symbols, types_utils


class Filter(types_utils.ContractsLanguageDunderMixin):
    def _validate_iterator(
        self, *, id_list: list[str], filter_variable_name: str, check_empty_variable: bool = True
    ):
        """
        All Filter classes should take an iterator attribute which is
        a list of string of IDs to be filtered on.

        :param id_list: the list of IDs to validate
        :param filter_variable_name: the string name of the variable for the given Filter
        :param check_empty_variable: check if filter variable entries are empty strings.
        This is to maintain existing behaviour for Balances/Flags/ParametersFilter.
        """
        iterator = types_utils.get_iterator(
            id_list,
            hint="str",
            name=f"{self.__class__.__name__}.{filter_variable_name}",
            check_empty=True,
        )

        id_set = set()
        duplicates_set = set()

        for i, id in enumerate(iterator):
            types_utils.validate_type(
                id,
                str,
                prefix=f"{self.__class__.__name__}.{filter_variable_name}[{i}]",
                check_empty=check_empty_variable,
            )

            if id in id_set:
                duplicates_set.add(id)
            else:
                id_set.add(id)

        if duplicates_set:
            raise exceptions.InvalidSmartContractError(
                f"'{self.__class__.__name__}.{filter_variable_name}' must not contain "
                f"any duplicates, got duplicates: {sorted(duplicates_set)}"
            )


class BalancesFilter(Filter):
    def __init__(self, *, addresses: list[str]):
        self.addresses = addresses
        self._validate_attributes()

    def _validate_attributes(self):
        self._validate_iterator(
            id_list=self.addresses, filter_variable_name="addresses", check_empty_variable=False
        )

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return types_utils.ClassSpec(
            name="BalancesFilter",
            docstring="A filter for refining the balances data retrieved by a fetcher.",
            public_attributes=cls._public_attributes(language_code),
            constructor=types_utils.ConstructorSpec(
                docstring="", args=cls._public_attributes(language_code)
            ),
        )

    @classmethod
    @lru_cache()
    def _public_attributes(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return [
            types_utils.ValueSpec(
                name="addresses", type="List[str]", docstring="A list of balance addresses."
            ),
        ]


class ParametersFilter(Filter):
    def __init__(self, *, parameter_ids: list[str]):
        self.parameter_ids = parameter_ids
        self._validate_attributes()

    def _validate_attributes(self):
        self._validate_iterator(
            id_list=self.parameter_ids,
            filter_variable_name="parameter_ids",
            check_empty_variable=False,
        )

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        spec = types_utils.ClassSpec(
            name="ParametersFilter",
            docstring="A filter for refining the parameters retrieved by a fetcher. Each ID here "
            "must correspond to the ID of an ExpectedParameter defined in the contract metadata.",
            public_attributes=cls._public_attributes(language_code),
            constructor=types_utils.ConstructorSpec(
                docstring="", args=cls._public_attributes(language_code)
            ),
        )
        return spec

    @classmethod
    @lru_cache()
    def _public_attributes(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return [
            types_utils.ValueSpec(
                name="parameter_ids",
                type="List[str]",
                docstring="A list of parameter IDs to fetch",
            ),
        ]


class FlagsFilter(Filter):
    def __init__(self, *, flag_definition_ids: list[str]):
        self.flag_definition_ids = flag_definition_ids
        self._validate_attributes()

    def _validate_attributes(self):
        self._validate_iterator(
            id_list=self.flag_definition_ids,
            filter_variable_name="flag_definition_ids",
            check_empty_variable=False,
        )

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        spec = types_utils.ClassSpec(
            name="FlagsFilter",
            docstring="A filter for refining the flags retrieved by a fetcher.",
            public_attributes=cls._public_attributes(language_code),
            constructor=types_utils.ConstructorSpec(
                docstring="", args=cls._public_attributes(language_code)
            ),
        )
        return spec

    @classmethod
    @lru_cache()
    def _public_attributes(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return [
            types_utils.ValueSpec(
                name="flag_definition_ids",
                type="List[str]",
                docstring="A list of flag definition ids to get flags for.",
            ),
        ]





class CalendarsFilter(Filter):
    def __init__(self, *, calendar_ids: list[str]):
        self.calendar_ids = calendar_ids
        self._validate_attributes()

    def _validate_attributes(self):
        self._validate_iterator(id_list=self.calendar_ids, filter_variable_name="calendar_ids")

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        spec = types_utils.ClassSpec(
            name="CalendarsFilter",
            docstring="A filter for refining the calendars retrieved by a fetcher.",
            public_attributes=cls._public_attributes(language_code),
            constructor=types_utils.ConstructorSpec(
                docstring="", args=cls._public_attributes(language_code)
            ),
        )
        return spec

    @classmethod
    @lru_cache()
    def _public_attributes(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return [
            types_utils.ValueSpec(
                name="calendar_ids",
                type="List[str]",
                docstring="A list of calendar IDs to get calendar events for.",
            ),
        ]


class EventTypesFilter(Filter):
    def __init__(self, *, event_types: list[str]):
        self.event_types = event_types
        self._validate_attributes()

    def _validate_attributes(self):
        self._validate_iterator(id_list=self.event_types, filter_variable_name="event_types")

    @classmethod
    @lru_cache()
    def _spec(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        spec = types_utils.ClassSpec(
            name="EventTypesFilter",
            docstring="A filter for refining the event types to fetch last scheduled event datetimes for.",
            public_attributes=cls._public_attributes(language_code),
            constructor=types_utils.ConstructorSpec(
                docstring="", args=cls._public_attributes(language_code)
            ),
        )
        return spec

    @classmethod
    @lru_cache()
    def _public_attributes(cls, language_code=symbols.Languages.ENGLISH):
        if language_code != symbols.Languages.ENGLISH:
            raise ValueError("Language not supported")

        return [
            types_utils.ValueSpec(
                name="event_types",
                type="List[str]",
                docstring="A list of `event_types` to retrieve last scheduled event datetimes for",
            ),
        ]
