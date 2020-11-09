import os
from collections import OrderedDict


class BIDSFilename(object):
    def __init__(self, raw_filename):
        self.__full_raw_filename = os.path.abspath(raw_filename)
        self.__dirname = os.path.dirname(self.__full_raw_filename)
        self.__basename = os.path.basename(self.__full_raw_filename)
        self.extension = ".".join(self.__basename.split(".")[1:])

        # convenient representation
        attribute_list_of_lists = [
            elem.split("-") for elem in self.__basename.split("_")
        ]

        self.attribute_dict = {
            sub_list[0]: sub_list[1]
            for sub_list in attribute_list_of_lists
            if len(sub_list) == 2
        }
        self.attributes_wo_keys = [
            sub_list[0].replace(f".{self.extension}", "")
            for sub_list in attribute_list_of_lists
            if len(sub_list) == 1
        ]
        self.attribute_order = [
            sub_list[0] for sub_list in attribute_list_of_lists if len(sub_list) == 2
        ]

    def __getattr__(self, attr_key):
        return self.attribute_dict[attr_key]

    # Generate new filename
    def get_basename(self):
        # sort the attribute dictionary using the attribute_order dictionary
        ordered_attr_dict = OrderedDict(
            sorted(
                self.attribute_dict.items(),
                key=lambda x: self.attribute_order.index(x[0]),
            )
        )
        # join the dictionary
        keyed_attr_string = "_".join(
            ["-".join([k, v]) for k, v in ordered_attr_dict.items()]
        )
        # join all of the attrs w/o keys
        non_keyed_attr_string = "_".join(self.attributes_wo_keys)
        return f"{keyed_attr_string}_{non_keyed_attr_string}.{self.extension}"

    def __str__(self):
        return os.path.join(self.__dirname, self.get_basename())

    # Create, Update, Delete attribute pairs
    def add_attribute(self, attr_key, attr_value):
        if attr_key not in self.attribute_dict.keys():
            self.attribute_dict[attr_key] = attr_value
            self.attribute_order.append(attr_key)
        else:
            raise ValueError("Value is already in the dict, use update_attribute")

    def update_attribute(self, attr_key, attr_value):
        try:
            assert attr_key in self.attribute_dict.keys()
            self.attribute_dict[attr_key] = attr_value
        except AssertionError as e:
            raise ValueError(f"Key {attr_key} cannot be updated as it is not in dict")

    def delete_attribute(self, attr_key):
        try:
            assert attr_key in self.attribute_dict.keys()
            self.attribute_dict.pop(attr_key)
            del self.attribute_order[self.attribute_order.index(attr_key)]
        except AssertionError as e:
            raise ValueError(f"Key {attr_key} not in attribute_dict")
