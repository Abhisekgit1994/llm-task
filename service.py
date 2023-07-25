import pandas as pd
import streamlit as st
from streamlit_ace import st_ace
from utils import LLMFunctions
llm = LLMFunctions()

st.set_page_config(layout='wide')
st.title('Candidate tables to Template table')
col1, col2 = st.columns([1, 3])


def main():
    st.session_state['selected_option'] = {}
    st.session_state['text'] = {}
    st.session_state['transformed_values'] = {}
    st.session_state['python_script'] = {}
    output_list = []
    track_output_prompt = []
    transformed_data = []  # store transformed data for all template columns
    failure_list = {}  # tracking script failures for each column and each selected option
    with col1:
        template = st.file_uploader('upload Template table', type=["csv"])
        if template:
            template_df = pd.read_csv(template)
            st.write(template_df.head(2))
    with col2:
        candidate = st.file_uploader('upload candidate table', type=["csv"])
        if candidate:
            candidate_df = pd.read_csv(candidate)
            st.write(candidate_df.head(2))
    if template and candidate:
        for col in template_df.columns:
            failure_list[col] = {}
            sub1, sub2, sub3 = col2.columns([1, 1.8, 1], gap="small")
            output, response, prompt = llm.find_similar_columns(reference_table=template_df.head(), candidate_table=candidate_df.head(), col=col)
            track_output_prompt.append({'prompt': prompt, 'completion': response})
            output_list.append(output)
            with col1:
                st.text(f'Similar columns for {col}')
                st.markdown(output['Candidate_table_similar_columns'])
                with st.expander("See Reason"):
                    st.markdown(output['Reason'])
            with col2:
                default_option = output['Candidate_table_similar_columns'][0]
                with sub1:
                    if col not in st.session_state.selected_option:
                        st.session_state.selected_option[col] = default_option
                    selected_option = st.selectbox(f'Select an option for {col}:', output['Candidate_table_similar_columns'])
                    st.session_state.selected_option[col] = selected_option
                    selected_data = candidate_df[selected_option].to_list()
                    st.write(f'Showing data for {selected_option}')
                    st.markdown(selected_data[:4])
                    response = llm.transform_values(template_df, col, candidate_df, selected_option)
                with sub2:
                    st.session_state.python_script[col] = {}
                    st.session_state.transformed_values[col] = {}
                    st.session_state.transformed_values[col][selected_option] = response['transformed_values']
                    st.session_state.python_script[col][selected_option] = response['python_script']
                    st.markdown('Python Script')
                    user_edit = st_ace(st.session_state.python_script[col][selected_option])
                    code = f"""{user_edit}"""
                    try:
                        exec(code, {'candidate_list': selected_data})
                    except Exception as e:
                        failure_list[col][selected_option] = e
                    st.session_state.python_script[col][selected_option] = user_edit  # updating the code in the session state
                    # transformed_data.append({col: response['transformed_values']})
                with sub3:
                    st.write(f'Showing transformed values for {st.session_state.selected_option[col]}')
                    st.write(response['transformed_values'])

        pd.DataFrame(transformed_data).to_csv('transformed_data.csv')
        return failure_list


if __name__ == "__main__":
    main()

