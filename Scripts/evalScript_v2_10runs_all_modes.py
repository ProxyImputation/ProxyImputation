import sklearn.neighbors._base
import sys
import os
import pandas as pd
import numpy as np
sys.modules['sklearn.neighbors.base'] = sklearn.neighbors._base
from missingpy import MissForest
from sklearn.metrics import mean_squared_error, mean_absolute_error

##########################################
#                                        #
#   Evaluation + mean calculation        #
#                                        #
##########################################


def read_csv_check_lines(file_path):
    # Read CSV file and return DataFrame.
    return pd.read_csv(file_path, sep=";")

def delete_values_at_random(df, column, percentage, indexes_to_delete=None):
    # Delete values from a DataFrame column based on a given percentage or provided indexes
    if indexes_to_delete is None:
        num_to_delete = int(len(df[column]) * (percentage / 100))
        indexes_to_delete = df[df[column].notnull()].sample(n=num_to_delete).index
    original_values = df.loc[indexes_to_delete, column].copy()
    df.loc[indexes_to_delete, column] = np.nan
    
    return df, original_values, indexes_to_delete
    
def delete_values_not_at_random(df, column, percentage):
    # Calculate the number of values to delete based on the percentage
    total_values = len(df[column].dropna())  # consider only non-NA values
    num_to_delete = int(total_values * (percentage / 100))
    
    # Identify values to delete: sort by the column, then take the first N values based on percentage
    sorted_indexes = df[column].sort_values().index[:num_to_delete]
    original_values = df.loc[sorted_indexes, column].copy()
    df.loc[sorted_indexes, column] = np.nan
    
    return df, original_values, sorted_indexes

def convert_categorical_to_numerical(df):
    for column in df.columns:
        if df[column].dtype == 'object':  # If column has categorical (string) data
            df[column] = df[column].astype('category').cat.codes + 1  # +1 to start codes from 1
    return df

def impute_with_miss_forest(df):
    # Exclude columns with all missing values
    cols_with_values = df.columns[df.notnull().any()].tolist()  # Columns with at least one non-missing value
    numeric_cols = df.select_dtypes(include=[np.number]).columns.intersection(cols_with_values)  # Keep only numeric

    if len(numeric_cols) == 0:
        print("No numeric columns with data available for imputation.")
        return df

    imputer = MissForest()
    df[numeric_cols] = imputer.fit_transform(df[numeric_cols])
    return df

def calculate_rmse_mae(original_values, imputed_values):
    # Calculate RMSE and MAE between original and imputed values.
    rmse = np.sqrt(mean_squared_error(original_values, imputed_values))
    mae = mean_absolute_error(original_values, imputed_values)
    return rmse, mae
    
def impute_with_mean(df, column_name, indexes):
    mean_value = df[column_name].mean()
    df.loc[indexes, column_name] = mean_value
    return df

def main(file1_path, file2_path, column_name, deletion_percentage, deletion_mode, catconv=False):
    # Read CSV files and check line counts
    df1 = read_csv_check_lines(file1_path)
    df2 = read_csv_check_lines(file2_path)
    
    # Convert categorical columns to numerical if catconv is True
    if catconv:
        df1 = convert_categorical_to_numerical(df1)
        df2 = convert_categorical_to_numerical(df2)

    # Check if column_name exists in both DataFrames
    if column_name not in df1.columns or column_name not in df2.columns:
        print(f"Column '{column_name}' does not appear in both CSV files. Exiting program.")
        sys.exit()

    if len(df1) != len(df2):
        print("The files have different numbers of lines. Exiting program.")
        return

    # Perform deletion depending on deletion mode
    if deletion_mode == 'random':
        df1, original_values1, indexes_deleted1 = delete_values_at_random(df1, column_name, deletion_percentage)
    elif deletion_mode == 'not_random':
        df1, original_values1, indexes_deleted1 = delete_values_not_at_random(df1, column_name, deletion_percentage)
    else:
        print(f"Invalid deletion mode: {deletion_mode}. Use 'random' or 'not_random'.")
        sys.exit()

    # For df2, we use the same indexes_deleted1 if deletion_mode is 'random' to ensure consistency
    if deletion_mode == 'random':
        df2, original_values2, _ = delete_values_at_random(df2, column_name, deletion_percentage, indexes_to_delete=indexes_deleted1)
    elif deletion_mode == 'not_random':
        df2, original_values2, _ = delete_values_not_at_random(df2, column_name, deletion_percentage)


    # Copy df1 for median imputation
    df1_copy = df1.copy()

    # Perform imputation
    df1_imputed = impute_with_miss_forest(df1)
    df2_imputed = impute_with_miss_forest(df2)
    df_mean_imputed = impute_with_mean(df1_copy, column_name, indexes_deleted1)

    # Extract imputed values from previously deleted indexes
    imputed_values1 = df1_imputed.loc[indexes_deleted1, column_name].values
    imputed_values2 = df2_imputed.loc[indexes_deleted1, column_name].values
    imputed_values_mean = df_mean_imputed.loc[indexes_deleted1, column_name].values
    print(imputed_values_mean)

    # Calculate RMSE and MAE
    rmse1, mae1 = calculate_rmse_mae(original_values1, imputed_values1)
    rmse2, mae2 = calculate_rmse_mae(original_values2, imputed_values2)
    mean_rmse, mean_mae = calculate_rmse_mae(original_values1, imputed_values_mean)

    return rmse1, mae1, rmse2, mae2, mean_rmse, mean_mae

def run_experiments(file1_path, file2_path, column_name, deletion_percentage, deletion_mode, catconv=False):
    rmse_results_file1 = []
    mae_results_file1 = []
    rmse_results_file2 = []
    mae_results_file2 = []
    mean_rmse_results = []
    mean_mae_results = []
    
    for _ in range(10):
        rmse1, mae1, rmse2, mae2, mean_rmse, mean_mae = main(file1_path, file2_path, column_name, deletion_percentage, deletion_mode, catconv)
        rmse_results_file1.extend([rmse1])
        rmse_results_file2.extend([rmse2])
        mean_rmse_results.extend([mean_rmse])
        mae_results_file1.extend([mae1])
        mae_results_file2.extend([mae2])
        mean_mae_results.extend([mean_mae])
        
    
    # Calculate average RMSE and MAE
    print(str(rmse_results_file1))
    print(str(rmse_results_file2))
    print(str(mean_rmse_results))
    print(str(mae_results_file1))
    print(str(mae_results_file2))
    print(str(mean_mae_results))
    
    
    avg_rmse_file1 = np.mean(rmse_results_file1)
    avg_rmse_file2 = np.mean(rmse_results_file2)
    avg_rmse_mean = np.mean(mean_rmse_results)
    avg_mae_file1 = np.mean(mae_results_file1)
    avg_mae_file2 = np.mean(mae_results_file2)
    avg_mae_mean = np.mean(mean_mae_results)
    
    # Save the average results to a file
    save_results_to_file(file1_path, rmse_results_file1, rmse_results_file2, avg_rmse_mean, mae_results_file1, mae_results_file2, avg_mae_mean, str(deletion_percentage), str(deletion_mode))
    print(f"Average RMSE file 1: {avg_rmse_file1}")
    print(f"Average RMSE file 2: {avg_rmse_file2}")
    print(f"Average RMSE mean : {avg_rmse_mean}")
    print(f"Average MAE file 1: {avg_mae_file1}")
    print(f"Average MAE file2 : {avg_mae_file2}")
    print(f"Average MAE mean : {avg_mae_mean}")
   

def save_results_to_file(file1_path, rmse_results_file1, rmse_results_file2, avg_rmse_mean, mae_results_file1, mae_results_file2, avg_mae_mean, percentage, deletion_mode):
    # Remove '.csv' from file1_path and append '_results.txt'
    base_name = os.path.splitext(file1_path)[0]
    results_file = f"{base_name}_results.txt"

    # Write results to file
    with open(results_file, 'a') as f:  # 'a' mode appends to the end of the file
        f.write(f"Percentage: {percentage}     Deletion Mode: {deletion_mode}\n")
        f.write(f"Average RMSE File 1, {np.mean(rmse_results_file1)}\n")
        f.write(f"Average RMSE File 2, {np.mean(rmse_results_file2)}\n")
        f.write(f"Average RMSE mean, {np.mean(avg_rmse_mean)}\n")
        f.write(f"Average MAE File 1, {np.mean(mae_results_file1)}\n")
        f.write(f"Average MAE File 2, {np.mean(mae_results_file2)}\n")
        f.write(f"Average MAE mean, {np.mean(avg_mae_mean)}\n")
        f.write(f"\n")

if __name__ == "__main__":
    if len(sys.argv) < 6:
        print("Usage: script.py <file1.csv> <file2.csv> <column_name> <deletion_percentage> <deletion_mode> [catconv]")
        sys.exit()
    
    file1_path = sys.argv[1]
    file2_path = sys.argv[2]
    column_name = sys.argv[3]
    deletion_percentage = float(sys.argv[4])
    deletion_mode = sys.argv[5]
    catconv = len(sys.argv) == 7 and sys.argv[6] == "catconv"

    # run_experiments(file1_path, file2_path, column_name, deletion_percentage, deletion_mode, catconv)
    run_experiments(file1_path, file2_path, column_name, 10, "random", "catconv")
    run_experiments(file1_path, file2_path, column_name, 20, "random", "catconv")
    run_experiments(file1_path, file2_path, column_name, 30, "random", "catconv")
    run_experiments(file1_path, file2_path, column_name, 40, "random", "catconv")
    run_experiments(file1_path, file2_path, column_name, 50, "random", "catconv")
    
    run_experiments(file1_path, file2_path, column_name, 10, "not_random", "catconv")
    run_experiments(file1_path, file2_path, column_name, 20, "not_random", "catconv")
    run_experiments(file1_path, file2_path, column_name, 30, "not_random", "catconv")
    run_experiments(file1_path, file2_path, column_name, 40, "not_random", "catconv")
    run_experiments(file1_path, file2_path, column_name, 50, "not_random", "catconv")
    

