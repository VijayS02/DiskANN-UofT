#pragma once

#include <vector>
#include "windows_customizations.h"
#include "tsl/robin_map.h"
#include "tsl/robin_set.h"
#include <abstract_filter_store.h>

namespace diskann {
  template<typename LabelT>
  class InMemFilterStore : public AbstractFilterStore<LabelT> {
   public:
    // Do nothing constructor because all the work is done in load()
    DISKANN_DLLEXPORT InMemFilterStore() {
    }

    /// <summary>
    /// Destructor
    /// </summary>
    DISKANN_DLLEXPORT virtual ~InMemFilterStore();

    // No copy, no assignment.
    DISKANN_DLLEXPORT InMemFilterStore<LabelT> &operator=(
        const InMemFilterStore<LabelT> &v) = delete;
    DISKANN_DLLEXPORT InMemFilterStore(const InMemFilterStore<LabelT> &v) =
        delete;

    DISKANN_DLLEXPORT virtual bool has_filter_support() const;

    /// <summary>
    /// Returns the filters for a data point. Only valid for base points
    /// </summary>
    /// <param name="point">base point id</param>
    /// <returns>list of filters of the base point</returns>
    DISKANN_DLLEXPORT virtual const std::vector<LabelT> &get_filters_for_point(
        location_t point) const override;

    /// <summary>
    /// Adds filters for a point.
    /// </summary>
    /// <param name="point"></param>
    /// <param name="filters"></param>
    DISKANN_DLLEXPORT virtual void add_filters_for_point(
        location_t point, const std::vector<LabelT> &filters) override;

    /// <summary>
    /// Returns a score between [0,1] indicating how many points in the dataset
    /// matched the predicate
    /// </summary>
    /// <param name="pred">Predicate to match</param>
    /// <returns>Score between [0,1] indicate %age of points matching
    /// pred</returns>
    DISKANN_DLLEXPORT virtual float get_predicate_selectivity(
        const AbstractPredicate &pred) const override;

    DISKANN_DLLEXPORT virtual const std::unordered_map<LabelT,
                                                       std::vector<location_t>>
        &get_label_to_medoids() const;

    DISKANN_DLLEXPORT virtual const std::vector<location_t>
        &get_medoids_of_label(const LabelT label) ;

    DISKANN_DLLEXPORT virtual void set_universal_label(const LabelT univ_label);

    DISKANN_DLLEXPORT inline bool point_has_label(location_t   point_id,
                                                  const LabelT label_id) const;

    DISKANN_DLLEXPORT inline bool is_dummy_point(location_t id) const;

    DISKANN_DLLEXPORT inline location_t get_real_point_for_dummy(
        location_t dummy_id);

    DISKANN_DLLEXPORT inline bool point_has_label_or_universal_label(
        location_t point_id, const LabelT label_id) const;

    DISKANN_DLLEXPORT inline LabelT get_converted_label(
        const std::string &filter_label);

    // Returns true if the index is filter-enabled and all files were loaded
    // correctly. false otherwise. Note that "false" can mean that the index
    // does not have filter support, or that some index files do not exist, or
    // that they exist and could not be opened.
    DISKANN_DLLEXPORT bool load(const std::string &disk_index_file);

    DISKANN_DLLEXPORT void generate_random_labels(std::vector<LabelT> &labels,
                                                  const uint32_t num_labels,
                                                  const uint32_t nthreads);

   private:
    // Load functions for search START
    void load_label_file(const std::string_view &file_content);
    void load_label_map(std::basic_istream<char> &map_reader);
    void load_labels_to_medoids(std::basic_istream<char> &reader);
    void load_dummy_map(std::basic_istream<char> &dummy_map_stream);
    void parse_universal_label(const std::string_view &content);
    void get_label_file_metadata(const std::string_view &fileContent,
                                 uint32_t &num_pts, uint32_t &num_total_labels);

    bool load_file_and_parse(const std::string &filename,
        void (InMemFilterStore::*parse_fn)(const std::string_view &content));
    bool parse_stream(
        const std::string &filename,
        void (InMemFilterStore::*parse_fn)(std::basic_istream<char> &stream));

    void reset_stream_for_reading(std::basic_istream<char> &infile);
    // Load functions for search END

    location_t                 _num_points = 0;     
    location_t                *_pts_to_label_offsets = nullptr;
    location_t                *_pts_to_label_counts = nullptr;
    LabelT                    *_pts_to_labels = nullptr;
    bool                       _use_universal_label = false;
    LabelT                     _universal_filter_label;
    tsl::robin_set<location_t> _dummy_pts;
    tsl::robin_set<location_t>         _has_dummy_pts;
    tsl::robin_map<location_t, location_t>              _dummy_to_real_map;
    tsl::robin_map<location_t, std::vector<location_t>> _real_to_dummy_map;
    std::unordered_map<std::string, LabelT>             _label_map;
    std::unordered_map<LabelT, std::vector<location_t>> _filter_to_medoid_ids;
    bool                                                _is_valid = false;
  };

}  // namespace diskann
