from typing import List, Dict
import timeit
import numpy as np
from scipy.sparse import csr_matrix

class NSSquares:
    """
    Generates and manages sparse triangular masks for binary operations.

    This class precomputes and stores sparse triangular masks as CSR matrices
    to optimize memory usage. Masks are generated based on bitwise operations
    and can be efficiently retrieved or created on demand.

    Attributes:
        masks (List[csr_matrix]): A list of precomputed sparse masks.
        max_power_of_two (int): The maximum power of 2 used for mask sizes.
        verbose (bool): Whether to print progress during mask generation.
        generation_times (Dict[int, float]): Timing data for mask generation.
    """

    def __init__(self, max_power_of_two: int = 2, verbose: bool = False) -> None:
        """
        Initializes the NSSquares generator with precomputed masks.

        :param max_power_of_two: The highest power of 2 to compute masks for.
        :type max_power_of_two: int
        :param verbose: Whether to print progress during mask generation.
        :type verbose: bool
        """
        self.masks: List[csr_matrix] = []  # List of precomputed sparse masks
        self.max_power_of_two = max_power_of_two  # Maximum power of 2 for mask size
        self.verbose = verbose  # Verbose output for debugging
        self.generation_times: Dict[int, float] = {}  # Timing data for mask generation
        self._precompute_masks()  # Precompute masks up to the specified size

    def __getitem__(self, index: int) -> csr_matrix:
        """
        Retrieves the sparse mask for the specified index.

        :param index: Index of the desired mask.
        :type index: int
        :return: The corresponding sparse mask.
        :rtype: csr_matrix
        """
        return self.get_mask(index)

    def _precompute_masks(self) -> None:
        """
        Precomputes sparse masks up to the size determined by 'max_power_of_two'.

        This method generates all necessary sparse masks in advance, up to
        the size defined by 'max_power_of_two'. The precomputation ensures
        efficient retrieval of masks during runtime.

        :return: None        :rtype:
        """
        max_size = 1 << self.max_power_of_two  # 2^max_power_of_two
        if self.verbose:
            print(f"Precomputing sparse masks up to size {max_size}x{max_size}...")
        for power in range(1, self.max_power_of_two + 1):
            size = 1 << power
            self._generate_masks_up_to(size)

    def _generate_masks_up_to(self, size: int) -> None:
        """
        Generates sparse masks up to the specified size.

        :param size: The upper bound for mask dimensions.
        :type size: int

        This method generates masks from the current size up to the specified size
        and records the time taken for the process.

        :return: None        :rtype:
        """
        start_time = timeit.default_timer()
        self.get_mask(size - 1)
        if self.verbose:
            elapsed_time = timeit.default_timer() - start_time
            self.generation_times[size] = elapsed_time
            print(f"Generated sparse masks up to size {size}x{size} in {elapsed_time:.4f} seconds.")

    def get_mask(self, index: int) -> csr_matrix:
        """
        Retrieves or generates the sparse mask for a given index.

        :param index: The index of the desired mask.
        :type index: int
        :return: The sparse mask for the given index.
        :rtype: csr_matrix
        :raises ValueError: If the index is negative.
        """
        if index < 0:
            raise ValueError("Mask index cannot be negative.")
        while len(self.masks) <= index:
            self.masks.append(self._create_sparse_triangle_mask(len(self.masks)))
        return self.masks[index]

    @staticmethod
    def _create_sparse_triangle_mask(target_value: int) -> csr_matrix:
        """
        Creates a sparse triangular mask based on bitwise operations.

        :param target_value: The target value for the mask.
        :type target_value: int
        :return: A 2D sparse boolean mask.
        :rtype: csr_matrix
        :raises ValueError: If the target value is negative.

        This function uses the bitwise OR operation to determine where
        entries in the mask should be set to True.
        """
        if target_value < 0:
            raise ValueError("Target value must be non-negative.")
        size = target_value + 1

        row_indices, col_indices = np.where(
            np.bitwise_or.outer(np.arange(size), np.arange(size)) == target_value
        )
        data = np.ones_like(row_indices, dtype=bool)
        return csr_matrix((data, (row_indices, col_indices)), shape=(size, size))
